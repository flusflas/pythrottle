import asyncio
import os
import time

import pytest
import uvloop

from pythrottle.throttle import Throttle, throttle, athrottle
from pythrottle.tests.profiler import Profiler

uvloop.install()
RATE = 10000
MAX_ERROR = float(os.getenv("THROTTLE_TEST_MAX_ERROR", "0.03")) / 100
TESTS_DURATION = 10


def current_test_name():
    """
    Returns the name of the current running test.

    :return: Name of the current running test.
    """
    return os.environ.get('PYTEST_CURRENT_TEST').split(':')[-1].split(' ')[0]


@pytest.fixture(name="throttle_obj")
def throttle_fxt():
    """
    Yields a :class:`Throttle` instance with the default rate.
    """
    yield Throttle(interval=(1 / RATE))


@pytest.fixture(name="profiler")
def profiler_fxt():
    """
    Yields a :class:`Profiler` instance with the default rate and number of
    iterations.
    """
    iter_count = TESTS_DURATION * RATE
    yield Profiler(iter_count, target_rate=RATE)


def log_results(measured_rate, error):
    """ Logs the measured rate and error. """
    test_name = current_test_name()
    print(f"{test_name} -> (Rate: {measured_rate}, Error: {100 * error:.3f}%)")


def assert_profiler_results(profiler: Profiler, throttle: Throttle,
                            max_error=MAX_ERROR):
    """
    Makes a series of default assertions with the :class:`Profiler` and
    :class:`Throttle` provided.

    :param profiler:  :class:`Profiler` instance with metrics of the test.
    :param throttle:  :class:`Throttle` instance after being used.
    :param max_error: Maximum rate error to pass the test. If not provided,
                      the default maximum error is used.
    """
    log_results(measured_rate=profiler.measured_rate, error=profiler.error)
    assert abs(profiler.error) < max_error
    assert throttle.ticks == profiler.iter_count


def test_sync_elapsed_exact(throttle_obj, profiler):
    """
    Tests the behavior of a Throttle instance using :func:`Throttle.elapsed`
    to wait between intervals with `exact` parameter equals to True.
    """
    with profiler:
        sleep_time = (0.01 / RATE) if (0.01 / RATE) < 0.001 else 0.001
        for _ in range(profiler.iter_count):
            while not throttle_obj.elapsed(exact=True):
                time.sleep(sleep_time)

    assert_profiler_results(profiler, throttle_obj)


def test_sync_elapsed_inexact():
    """
    Tests the behavior of a Throttle instance using :func:`Throttle.elapsed`
    to wait between intervals with `exact` parameter equals to False.
    """
    rate = 5
    simulated_rate = 4
    max_error = 0.01
    throttle_obj = Throttle(interval=(1 / rate))
    iter_count = TESTS_DURATION * rate

    with Profiler(iter_count, target_rate=simulated_rate) as profiler:
        for _ in range(iter_count):
            while not throttle_obj.elapsed(exact=False):
                time.sleep(1 / simulated_rate)

    assert_profiler_results(profiler, throttle_obj, max_error)


def test_sync_wait_next(throttle_obj, profiler):
    """
    Tests the behavior of a Throttle instance using
    :func:`Throttle.wait_next` to wait between intervals.
    """
    with profiler:
        for _ in range(profiler.iter_count):
            throttle_obj.wait_next()

    assert_profiler_results(profiler, throttle_obj)


def test_sync_loop_no_arguments(throttle_obj, profiler):
    """
    Tests the behavior of a Throttle instance using :func:`Throttle.loop`
    to iterate between intervals without arguments.
    """
    ticks = -1
    with profiler:
        for i in throttle_obj.loop():
            ticks += 1
            assert ticks == i
            if ticks == profiler.iter_count - 1:
                break

    assert_profiler_results(profiler, throttle_obj)


def test_sync_loop_max_ticks(throttle_obj, profiler):
    """
    Tests the behavior of a Throttle instance using
    :func:`Throttle.loop` to iterate between intervals for a
    maximum number of iterations.
    """
    ticks = -1
    with profiler:
        for i in throttle_obj.loop(max_ticks=profiler.iter_count):
            ticks += 1
            assert ticks == i

    assert_profiler_results(profiler, throttle_obj)
    assert i == profiler.iter_count - 1


def test_sync_loop_duration(throttle_obj, profiler):
    """
    Tests the behavior of a Throttle instance using
    :func:`Throttle.loop` to iterate between intervals for a
    maximum amount of time.
    """
    ticks = -1
    with profiler:
        for i in throttle_obj.loop(duration=TESTS_DURATION):
            ticks += 1
            assert ticks == i

    assert_profiler_results(profiler, throttle_obj)
    assert i == profiler.iter_count - 1


def test_sync_loop_invalid_params(throttle_obj, profiler):
    """
    Tests the behavior of a Throttle instance using
    :func:`Throttle.loop` with invalid parameters.
    """
    with pytest.raises(ValueError):
        with profiler:
            gen = throttle_obj.loop(max_ticks=profiler.iter_count,
                                    duration=TESTS_DURATION)
            next(gen)


def test_restart(throttle_obj, profiler):
    """
    Tests the behavior of a single Throttle instance iterating during two
    periods of time separate separated by a short sleep. After this break,
    the Throttle is restarted to check that the behavior is the same in
    the two periods.
    """
    ticks = -1
    with profiler:
        for i in throttle_obj.loop(max_ticks=profiler.iter_count):
            ticks += 1
            assert ticks == i

    assert_profiler_results(profiler, throttle_obj)
    assert i == profiler.iter_count - 1

    time.sleep(1)
    throttle_obj.restart()
    ticks = -1

    with profiler:
        for i in throttle_obj.loop(max_ticks=profiler.iter_count):
            ticks += 1
            assert ticks == i

    assert_profiler_results(profiler, throttle_obj)
    assert i == profiler.iter_count - 1


def test_no_restart(throttle_obj, profiler):
    """
    Tests the behavior of a single Throttle instance iterating during two
    periods of time separate separated by a short sleep. After this break,
    the Throttle is not restarted. This should make the second period to
    be shorter as the Throttle tries to reach its internal rate, and
    therefore the metrics in this period should be different.
    """
    rest_time = 1
    ticks = -1

    with profiler:
        for i in throttle_obj.loop(max_ticks=profiler.iter_count):
            ticks += 1
            assert ticks == i

    assert_profiler_results(profiler, throttle_obj)
    assert i == profiler.iter_count - 1

    time.sleep(rest_time)
    ticks = -1

    with profiler:
        for i in throttle_obj.loop(max_ticks=profiler.iter_count):
            ticks += 1
            assert ticks == i

    expected_rate = profiler.iter_count / (TESTS_DURATION - rest_time)
    error = 1 - profiler.measured_rate / expected_rate
    max_error = 0.001

    log_results(measured_rate=profiler.measured_rate, error=error)
    assert abs(error) < max_error
    assert throttle_obj.ticks == 2 * profiler.iter_count
    assert i == profiler.iter_count - 1


@pytest.mark.asyncio
async def test_async_await_next(throttle_obj, profiler):
    """
    Tests the behavior of a Throttle instance using
    :func:`Throttle.await_next` to wait between intervals.
    """
    with profiler:
        for _ in range(profiler.iter_count):
            await throttle_obj.await_next()

    assert_profiler_results(profiler, throttle_obj)


@pytest.mark.asyncio
async def test_async_await_next_tasks(throttle_obj, profiler):
    """
    Tests the behavior of a Throttle instance using
    :func:`Throttle.await_next` to wait between intervals.
    For each interval, an asynchronous task is created.
    """

    async def aux_task(m: Throttle):
        await m.await_next()

    # Split async tasks in chunks to avoid large number of tasks in the loop
    # (which reduce performace for high rates and distorts the test)
    remaining = profiler.iter_count
    max_tasks = 100

    with profiler:
        while remaining > 0:
            size = remaining if remaining < max_tasks else max_tasks
            remaining -= size
            await asyncio.gather(*(aux_task(throttle_obj)
                                   for _ in range(size)))

    assert_profiler_results(profiler, throttle_obj)


@pytest.mark.asyncio
async def test_sync_aloop_no_arguments(throttle_obj, profiler):
    """
    Tests the behavior of a Throttle instance using :func:`Throttle.aloop`
    to iterate between intervals without arguments.
    """
    ticks = -1
    with profiler:
        async for i in throttle_obj.aloop():
            ticks += 1
            assert ticks == i
            if ticks == profiler.iter_count - 1:
                break

    assert_profiler_results(profiler, throttle_obj)


@pytest.mark.asyncio
async def test_async_aloop_max_ticks(throttle_obj, profiler):
    """
    Tests the behavior of a Throttle instance using
    :func:`Throttle.aloop` to iterate between intervals for a
    maximum number of iterations.
    """
    ticks = -1
    with profiler:
        async for i in throttle_obj.aloop(max_ticks=profiler.iter_count):
            ticks += 1
            assert ticks == i

    assert_profiler_results(profiler, throttle_obj)
    assert i == profiler.iter_count - 1


@pytest.mark.asyncio
async def test_async_aloop_duration(throttle_obj, profiler):
    """
    Tests the behavior of a Throttle instance using
    :func:`Throttle.aloop` to iterate between intervals for a
    maximum amount of time.
    """
    ticks = -1
    with profiler:
        async for i in throttle_obj.aloop(duration=TESTS_DURATION):
            ticks += 1
            assert ticks == i

    assert_profiler_results(profiler, throttle_obj)
    assert i == profiler.iter_count - 1


@pytest.mark.asyncio
async def test_async_loop_invalid_params(throttle_obj, profiler):
    """
    Tests the behavior of a Throttle instance using
    :func:`Throttle.aloop` with invalid parameters.
    """
    with pytest.raises(ValueError):
        with profiler:
            gen = throttle_obj.aloop(max_ticks=profiler.iter_count,
                                     duration=TESTS_DURATION)
            await gen.__anext__()


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
    def func():
        return "OK"

    for i in range(23):
        result = func()
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
    def func():
        return "OK"

    with Profiler() as profiler:
        for _ in range(25):
            result = func()
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
    def func():
        return "OK"

    await assert_async_decorator_error(call_counter, fail_counter, func)


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
    async def func():
        return "OK"

    await assert_async_decorator_error(call_counter, fail_counter, func)


async def assert_async_decorator_error(call_counter, fail_counter, func):
    """
    Helper function for :func:`test_async_decorator_sync_error`
    and :func:`test_async_decorator_async_error`.
    """
    for _ in range(23):
        result = await func()
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
    async def func():
        return "OK"

    for _ in range(23):
        result = await func()
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
    async def func():
        return "OK"

    with Profiler() as profiler:
        for _ in range(25):
            result = await func()
            if result:
                call_counter += 1

    assert call_counter == 25
    assert abs(profiler.elapsed_error(2.0)) < 0.001


def test_nested_sync_decorators():
    """
    Tests nesting of two :func:`throttle` decorators to set two call
    limits for a single synchronous function.
    """
    call_counter = 0
    fail_counter_1 = 0
    fail_counter_2 = 0

    @throttle(limit=2, interval=0.1, on_fail="FAIL_1")
    @throttle(limit=3, interval=0.2, on_fail="FAIL_2")
    def func():
        return "OK"

    for _ in Throttle(interval=0.01).loop(100):
        result = func()
        if result == "OK":
            call_counter += 1
        elif result == "FAIL_1":
            fail_counter_1 += 1
        elif result == "FAIL_2":
            fail_counter_2 += 1

    assert call_counter == 15
    assert fail_counter_1 == 80
    assert fail_counter_2 == 5


@pytest.mark.asyncio
async def test_nested_async_decorators():
    """
    Tests nesting of two :func:`athrottle` decorators to set two call
    limits for a single asynchronous function.
    """
    call_counter = 0
    fail_counter_1 = 0
    fail_counter_2 = 0

    @athrottle(limit=2, interval=0.1, on_fail="FAIL_1")
    @athrottle(limit=3, interval=0.2, on_fail="FAIL_2")
    async def func():
        return "OK"

    async for _ in Throttle(interval=0.01).aloop(100):
        result = await func()
        if result == "OK":
            call_counter += 1
        elif result == "FAIL_1":
            fail_counter_1 += 1
        elif result == "FAIL_2":
            fail_counter_2 += 1

    assert call_counter == 15
    assert fail_counter_1 == 80
    assert fail_counter_2 == 5
