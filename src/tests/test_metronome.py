import asyncio
import time

import pytest
import uvloop

from src.metronome import Metronome

uvloop.install()
rate = 100000
MAX_ERROR = 0.03


def test_sync_elapsed():
    met = Metronome(interval=(1 / rate), exact=True)
    iter_count = 4 * rate
    t_start = time.perf_counter()
    sleep_time = (0.01 / rate) if (0.01 / rate) < 0.001 else 0.001
    for i in range(iter_count):
        while not met.elapsed():
            time.sleep(sleep_time)

    t_end = time.perf_counter()
    elapsed = t_end - t_start
    measured_rate = iter_count / elapsed
    error = 100 * (1 - measured_rate / rate)

    print(f"Sync Rate: {measured_rate}, Error: {error:.3f}%")
    assert abs(error) < MAX_ERROR


def test_sync_sleep():
    met = Metronome(interval=(1 / rate), exact=True)
    iter_count = 4 * rate
    t_start = time.perf_counter()
    for i in range(iter_count):
        met.sleep_until_available()

    t_end = time.perf_counter()
    elapsed = t_end - t_start
    measured_rate = iter_count / elapsed
    error = 100 * (1 - measured_rate / rate)

    print(f"Sync Rate: {measured_rate}, Error: {error:.3f}%")
    assert abs(error) < MAX_ERROR


@pytest.mark.asyncio
async def test_async_wait():
    met = Metronome(interval=(1 / rate), exact=True)
    iter_count = 4 * rate
    t_start = time.perf_counter()
    # Split async tasks in chunks to avoid large number of tasks in the loop
    # (which reduce performace for high rates and distorts the test)
    remaining = iter_count
    max_tasks = 100
    while remaining > 0:
        size = remaining if remaining < max_tasks else max_tasks
        remaining -= size
        await asyncio.gather(*(aux_test_async_wait(met) for _ in range(size)))
    t_end = time.perf_counter()
    elapsed = t_end - t_start
    measured_rate = iter_count / elapsed
    error = 100 * (1 - measured_rate / rate)
    print(f"Async Rate: {measured_rate}, Error: {error:.3f}%")
    assert abs(error) < MAX_ERROR


async def aux_test_async_wait(met: Metronome):
    await met.wait_until_available()
