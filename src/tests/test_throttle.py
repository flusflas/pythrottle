import asyncio
import os
import time

import pytest
import uvloop

from src.throttle import Throttle, throttle, athrottle
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


@pytest.fixture
def throttle_fxt():
    """
    Yields a :class:`Throttle` instance with the default rate.
    """
    yield Throttle(interval=(1 / RATE))


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


def assert_profiler_results(profiler: Profiler, throttle: Throttle,
                            max_error=MAX_ERROR):
    """
    Makes a series of default assertions with the :class:`Profiler` and
    :class:`Throttle` provided.

    :param profiler:  :class:`Profiler` instance with metrics of the test.
    :param throttle: :class:`Throttle` instance after being used.
    :param max_error: Maximum rate error to pass the test. If not provided,
                      the default maximum error is used.
    """
    log_results(measured_rate=profiler.measured_rate, error=profiler.error)
    assert abs(profiler.error) < max_error
    assert throttle.ticks == profiler.iter_count


def test_sync_elapsed_exact(throttle_fxt, profiler):
    with profiler:
        sleep_time = (0.01 / RATE) if (0.01 / RATE) < 0.001 else 0.001
        for i in range(profiler.iter_count):
            while not throttle_fxt.elapsed(exact=True):
                time.sleep(sleep_time)

    assert_profiler_results(profiler, throttle_fxt)


def test_sync_elapsed_inexact():
    rate = 5
    simulated_rate = 4
    max_error = 0.01
    throttle_fxt = Throttle(interval=(1 / rate))
    iter_count = TESTS_DURATION * rate

    with Profiler(iter_count, target_rate=simulated_rate) as profiler:
        for i in range(iter_count):
            while not throttle_fxt.elapsed(exact=False):
                time.sleep(1 / simulated_rate)

    assert_profiler_results(profiler, throttle_fxt, max_error)


def test_sync_sleep(throttle_fxt, profiler):
    with profiler:
        for i in range(profiler.iter_count):
            throttle_fxt.sleep_until_available()

    assert_profiler_results(profiler, throttle_fxt)


def test_sync_sleep_loop(throttle_fxt, profiler):
    with profiler:
        for i in throttle_fxt.sleep_loop(max_ticks=profiler.iter_count):
            pass

    assert_profiler_results(profiler, throttle_fxt)
    assert i == profiler.iter_count


def test_restart(throttle_fxt, profiler):
    """
    Tests the behavior of a single Throttle instance iterating during two
    periods of time separate separated by a short sleep. After this break,
    the Throttle is restarted to check that the behavior is the same in
    the two periods.
    """
    with profiler:
        for i in throttle_fxt.sleep_loop(max_ticks=profiler.iter_count):
            pass

    assert_profiler_results(profiler, throttle_fxt)
    assert i == profiler.iter_count

    time.sleep(1)
    throttle_fxt.restart()

    with profiler:
        for i in throttle_fxt.sleep_loop(max_ticks=profiler.iter_count):
            pass

    assert_profiler_results(profiler, throttle_fxt)
    assert i == profiler.iter_count


def test_no_restart(throttle_fxt, profiler):
    """
    Tests the behavior of a single Throttle instance iterating during two
    periods of time separate separated by a short sleep. After this break,
    the Throttle is not restarted. This should make the second period to
    be shorter as the Throttle tries to reach its internal rate, and
    therefore the metrics in this period should be different.
    """
    rest_time = 1

    with profiler:
        for i in throttle_fxt.sleep_loop(max_ticks=profiler.iter_count):
            pass

    assert_profiler_results(profiler, throttle_fxt)
    assert i == profiler.iter_count

    time.sleep(rest_time)

    with profiler:
        for i in throttle_fxt.sleep_loop(max_ticks=profiler.iter_count):
            pass

    expected_rate = profiler.iter_count / (TESTS_DURATION - rest_time)
    error = 1 - profiler.measured_rate / expected_rate
    max_error = 0.001

    log_results(measured_rate=profiler.measured_rate, error=error)
    assert abs(error) < max_error
    assert throttle_fxt.ticks == 2 * profiler.iter_count
    assert i == profiler.iter_count


@pytest.mark.asyncio
async def test_async_wait(throttle_fxt, profiler):
    with profiler:
        for i in range(profiler.iter_count):
            await throttle_fxt.wait_until_available()

    assert_profiler_results(profiler, throttle_fxt)


@pytest.mark.asyncio
async def test_async_wait_tasks(throttle_fxt, profiler):
    async def aux_task(m: Throttle):
        await m.wait_until_available()

    # Split async tasks in chunks to avoid large number of tasks in the loop
    # (which reduce performace for high rates and distorts the test)
    remaining = profiler.iter_count
    max_tasks = 100

    with profiler:
        while remaining > 0:
            size = remaining if remaining < max_tasks else max_tasks
            remaining -= size
            await asyncio.gather(*(aux_task(throttle_fxt) for _ in range(size)))

    assert_profiler_results(profiler, throttle_fxt)


@pytest.mark.asyncio
async def test_async_wait_loop(throttle_fxt, profiler):
    with profiler:
        async for i in throttle_fxt.wait_loop(max_ticks=profiler.iter_count):
            i += 0      # Coverage ignores 'pass' in this async loop ¬¬

    assert_profiler_results(profiler, throttle_fxt)
    assert i == profiler.iter_count


def test_sync_decorator():
    """
    Tests the :func:`throttle` decorator over a synchronous function
    with `on_fail` parameter.
    """
    call_counter = 0
    fail_counter = 0

    def on_fail():
        return "Error"

    @throttle(limit=5, interval=1, on_fail=on_fail)
    def foo():
        return "OK"

    for i in range(23):
        result = foo()
        if result == "OK":
            call_counter += 1
        else:
            fail_counter += 1
        time.sleep(0.1)

    assert call_counter == 13
    assert fail_counter == 10


def test_sync_decorator_wait():
    """
    Tests the :func:`throttle` decorator over a synchronous function
    with `wait` parameter equal to True.
    """
    call_counter = 0

    @throttle(limit=5, interval=0.5, wait=True)
    def foo():
        return "OK"

    with Profiler() as profiler:
        for i in range(25):
            result = foo()
            if result:
                call_counter += 1

    assert call_counter == 25
    assert abs(profiler.elapsed_error(2.0)) < 0.001


@pytest.mark.asyncio
async def test_async_decorator_sync_error():
    """
    Tests the :func:`athrottle` decorator over a synchronous function
    with a synchronous funcion as `on_fail` parameter.
    """
    call_counter = 0
    fail_counter = 0

    def on_fail():
        return "Error"

    @athrottle(limit=5, interval=1, on_fail=on_fail)
    def foo():
        return "OK"

    for i in range(23):
        result = await foo()
        if result == "OK":
            call_counter += 1
        else:
            fail_counter += 1
        time.sleep(0.1)

    assert call_counter == 13
    assert fail_counter == 10


@pytest.mark.asyncio
async def test_async_decorator_async_error():
    """
    Tests the :func:`athrottle` decorator over an asynchronous function
    with an asynchronous function as `on_fail` parameter.
    """
    call_counter = 0
    fail_counter = 0

    async def on_fail():
        return "Error"

    @athrottle(limit=5, interval=1, on_fail=on_fail)
    async def foo():
        return "OK"

    for i in range(23):
        result = await foo()
        if result == "OK":
            call_counter += 1
        else:
            fail_counter += 1
        time.sleep(0.1)

    assert call_counter == 13
    assert fail_counter == 10


@pytest.mark.asyncio
async def test_async_decorator_value_error():
    """
    Tests the :func:`athrottle` decorator over an asynchronous function
    with a non-function value as `on_fail` parameter.
    """
    call_counter = 0
    fail_counter = 0

    @athrottle(limit=5, interval=1, on_fail=7)
    async def foo():
        return "OK"

    for i in range(23):
        result = await foo()
        if result == "OK":
            call_counter += 1
        elif result == 7:
            fail_counter += 1
        time.sleep(0.1)

    assert call_counter == 13
    assert fail_counter == 10


@pytest.mark.asyncio
async def test_async_decorator_wait():
    """
    Tests the :func:`athrottle` decorator over an asynchronous function
    with `wait` parameter equal to True.
    """
    call_counter = 0

    @athrottle(limit=5, interval=0.5, wait=True)
    async def foo():
        return "OK"

    with Profiler() as profiler:
        for i in range(25):
            result = await foo()
            if result:
                call_counter += 1

    assert call_counter == 25
    assert abs(profiler.elapsed_error(2.0)) < 0.001
