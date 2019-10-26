import asyncio
import time

import pytest
import uvloop

from src.metronome import Metronome

uvloop.install()
RATE = 100000
MAX_ERROR = 0.03
TESTS_DURATION = 5


def test_sync_elapsed_exact():
    met = Metronome(interval=(1 / RATE))
    iter_count = TESTS_DURATION * RATE
    t_start = time.perf_counter()
    sleep_time = (0.01 / RATE) if (0.01 / RATE) < 0.001 else 0.001
    for i in range(iter_count):
        while not met.elapsed(exact=True):
            time.sleep(sleep_time)

    t_end = time.perf_counter()
    elapsed = t_end - t_start
    measured_rate = iter_count / elapsed
    error = 100 * (1 - measured_rate / RATE)

    print(f"Sync Rate: {measured_rate}, Error: {error:.3f}%")
    assert abs(error) < MAX_ERROR


def test_sync_elapsed_inexact():
    rate = 5
    simulated_rate = 4
    met = Metronome(interval=(1 / rate))
    iter_count = TESTS_DURATION * rate
    t_start = time.perf_counter()
    for i in range(iter_count):
        while not met.elapsed(exact=False):
            time.sleep(1 / simulated_rate)

    t_end = time.perf_counter()
    elapsed = t_end - t_start
    measured_rate = iter_count / elapsed
    error = 100 * (1 - measured_rate / simulated_rate)

    print(f"Sync Rate: {measured_rate}, Error: {error:.3f}%")
    assert abs(error) < 1.0


def test_sync_sleep():
    met = Metronome(interval=(1 / RATE))
    iter_count = TESTS_DURATION * RATE
    t_start = time.perf_counter()
    for i in range(iter_count):
        met.sleep_until_available()

    t_end = time.perf_counter()
    elapsed = t_end - t_start
    measured_rate = iter_count / elapsed
    error = 100 * (1 - measured_rate / RATE)

    print(f"Sync Rate: {measured_rate}, Error: {error:.3f}%")
    assert abs(error) < MAX_ERROR


@pytest.mark.asyncio
async def test_async_wait():
    met = Metronome(interval=(1 / RATE))
    iter_count = TESTS_DURATION * RATE
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
    error = 100 * (1 - measured_rate / RATE)
    print(f"Async Rate: {measured_rate}, Error: {error:.3f}%")
    assert abs(error) < MAX_ERROR


async def aux_test_async_wait(met: Metronome):
    await met.wait_until_available()
