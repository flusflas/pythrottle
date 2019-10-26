import asyncio
import time

import pytest
import uvloop

from src.metronome import Metronome
from src.tests.profiler import Profiler

uvloop.install()
RATE = 10000
MAX_ERROR = 0.03 / 100
TESTS_DURATION = 5


def test_interval_missing():
    met = Metronome()
    with pytest.raises(ValueError):
        met.elapsed()


def test_sync_elapsed_exact():
    met = Metronome(interval=(1 / RATE))
    iter_count = TESTS_DURATION * RATE

    with Profiler(iter_count, target_rate=RATE) as profiler:
        sleep_time = (0.01 / RATE) if (0.01 / RATE) < 0.001 else 0.001
        for i in range(iter_count):
            while not met.elapsed(exact=True):
                time.sleep(sleep_time)

    print(f"Rate: {profiler.measured_rate}, Error: {100 * profiler.error:.3f}%")
    assert abs(profiler.error) < MAX_ERROR
    assert met.ticks == iter_count


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

    print(f"Rate: {profiler.measured_rate}, Error: {100 * profiler.error:.3f}%")
    assert abs(profiler.error) < max_error
    assert met.ticks == iter_count


def test_sync_sleep():
    met = Metronome(interval=(1 / RATE))
    iter_count = TESTS_DURATION * RATE

    with Profiler(iter_count, target_rate=RATE) as profiler:
        for i in range(iter_count):
            met.sleep_until_available()

    print(f"Rate: {profiler.measured_rate}, Error: {100 * profiler.error:.3f}%")
    assert abs(profiler.error) < MAX_ERROR
    assert met.ticks == iter_count


@pytest.mark.asyncio
async def test_async_wait():
    met = Metronome(interval=(1 / RATE))
    iter_count = TESTS_DURATION * RATE

    async def aux_task(m: Metronome):
        await m.wait_until_available()

    # Split async tasks in chunks to avoid large number of tasks in the loop
    # (which reduce performace for high rates and distorts the test)
    remaining = iter_count
    max_tasks = 100

    with Profiler(iter_count, target_rate=RATE) as profiler:
        while remaining > 0:
            size = remaining if remaining < max_tasks else max_tasks
            remaining -= size
            await asyncio.gather(*(aux_task(met) for _ in range(size)))

    print(f"Rate: {profiler.measured_rate}, Error: {100 * profiler.error:.3f}%")
    assert abs(profiler.error) < MAX_ERROR
    assert met.ticks == iter_count
