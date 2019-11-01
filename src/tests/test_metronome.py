import asyncio
import os
import time

import pytest
import uvloop

from src.metronome import Metronome
from src.tests.profiler import Profiler

uvloop.install()
RATE = 10000
MAX_ERROR = 0.03 / 100
TESTS_DURATION = 5


def current_test_name():
    """
    Returns the name of the current running test.

    :return: Name of the current running test.
    """
    return os.environ.get('PYTEST_CURRENT_TEST').split(':')[-1].split(' ')[0]


@pytest.fixture(name="met")
def metronome():
    """
    Yields a :class:`Metronome` instance with the default rate.
    """
    yield Metronome(interval=(1 / RATE))


@pytest.fixture
def profiler():
    """
    Yields a :class:`Profiler` instance with the default rate and number of
    iterations.
    """
    iter_count = TESTS_DURATION * RATE
    profiler = Profiler(iter_count, target_rate=RATE)
    yield profiler


def log_results(measured_rate, error):
    test_name = current_test_name()
    print(f"{test_name} -> (Rate: {measured_rate}, Error: {100 * error:.3f}%)")


def assert_profiler_results(profiler: Profiler, metronome: Metronome,
                            max_error=MAX_ERROR):
    """
    Makes a series of default assertions with the :class:`Profiler` and
    :class:`Metronome` provided.

    :param profiler:  :class:`Profiler` instance with metrics of the test.
    :param metronome: :class:`Metronome` instance after being used.
    :param max_error: Maximum rate error to pass the test. If not provided,
                      the default maximum error is used.
    """
    log_results(measured_rate=profiler.measured_rate, error=profiler.error)
    assert abs(profiler.error) < max_error
    assert metronome.ticks == profiler.iter_count


def test_sync_elapsed_exact(met, profiler):
    with profiler:
        sleep_time = (0.01 / RATE) if (0.01 / RATE) < 0.001 else 0.001
        for i in range(profiler.iter_count):
            while not met.elapsed(exact=True):
                time.sleep(sleep_time)

    assert_profiler_results(profiler, met)


def test_sync_elapsed_inexact():
    rate = 5
    simulated_rate = 4
    max_error = 0.01
    met = Metronome(interval=(1 / rate))
    iter_count = TESTS_DURATION * rate

    with Profiler(iter_count, target_rate=simulated_rate) as profiler:
        for i in range(iter_count):
            while not met.elapsed(exact=False):
                time.sleep(1 / simulated_rate)

    assert_profiler_results(profiler, met, max_error)


def test_sync_sleep(met, profiler):
    with profiler:
        for i in range(profiler.iter_count):
            met.sleep_until_available()

    assert_profiler_results(profiler, met)


def test_sync_sleep_loop(met, profiler):
    with profiler:
        for i in met.sleep_loop(max_ticks=profiler.iter_count):
            pass

    assert_profiler_results(profiler, met)
    assert i == profiler.iter_count


def test_restart(met, profiler):
    """
    Tests the behavior of a single Metronome instance iterating during two
    periods of time separate separated by a short sleep. After this break,
    the Metronome is restarted to check that the behavior is the same in
    the two periods.
    """
    with profiler:
        for i in met.sleep_loop(max_ticks=profiler.iter_count):
            pass

    assert_profiler_results(profiler, met)
    assert i == profiler.iter_count

    time.sleep(1)
    met.restart()

    with profiler:
        for i in met.sleep_loop(max_ticks=profiler.iter_count):
            pass

    assert_profiler_results(profiler, met)
    assert i == profiler.iter_count


def test_no_restart(met, profiler):
    """
    Tests the behavior of a single Metronome instance iterating during two
    periods of time separate separated by a short sleep. After this break,
    the Metronome is not restarted. This should make the second period to
    be shorter as the Metronome tries to reach its internal rate, and
    therefore the metrics in this period should be different.
    """
    rest_time = 1

    with profiler:
        for i in met.sleep_loop(max_ticks=profiler.iter_count):
            pass

    assert_profiler_results(profiler, met)
    assert i == profiler.iter_count

    time.sleep(rest_time)

    with profiler:
        for i in met.sleep_loop(max_ticks=profiler.iter_count):
            pass

    expected_rate = profiler.iter_count / (TESTS_DURATION - rest_time)
    error = 1 - profiler.measured_rate / expected_rate
    max_error = 0.001

    log_results(measured_rate=profiler.measured_rate, error=error)
    assert abs(error) < max_error
    assert met.ticks == 2 * profiler.iter_count
    assert i == profiler.iter_count


@pytest.mark.asyncio
async def test_async_wait(met, profiler):
    with profiler:
        for i in range(profiler.iter_count):
            await met.wait_until_available()

    assert_profiler_results(profiler, met)


@pytest.mark.asyncio
async def test_async_wait_tasks(met, profiler):
    async def aux_task(m: Metronome):
        await m.wait_until_available()

    # Split async tasks in chunks to avoid large number of tasks in the loop
    # (which reduce performace for high rates and distorts the test)
    remaining = profiler.iter_count
    max_tasks = 100

    with profiler:
        while remaining > 0:
            size = remaining if remaining < max_tasks else max_tasks
            remaining -= size
            await asyncio.gather(*(aux_task(met) for _ in range(size)))

    assert_profiler_results(profiler, met)


@pytest.mark.asyncio
async def test_async_wait_loop(met, profiler):
    with profiler:
        async for i in met.wait_loop(max_ticks=profiler.iter_count):
            pass

    assert_profiler_results(profiler, met)
    assert i == profiler.iter_count
