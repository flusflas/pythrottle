import asyncio
import inspect
import math
from functools import wraps
from time import perf_counter, sleep


class Throttle:
    """
    This class offers synchronous and asynchronous mechanisms to
    accurately rate-limit the execution of some iterative code.
    It can be used explicitly to wait between each time interval or
    with generator functions to iterate through intervals.

    Example: Video recorder at 24 fps. Each iteration in the loop
    starts precisely every 1/24 seconds (if the iterations don't last
    longer).

    >>> rate = 24   # fps
    >>> throttle = Throttle(interval=(1 / rate))
    >>> iters = 0
    >>> t_start = perf_counter()
    >>> for i in throttle.loop(24):
    ...     # Take, process and save image
    ...     iters += 1
    >>> total_time = round(perf_counter() - t_start, 2)
    >>> print('iters: {}, total_time: {}'.format(iters, total_time))
    iters: 24, total_time: 1.0
    """

    def __init__(self, interval):
        """
        Returns a :class:`Throttle` instance. Time reference will be set the
        first time a timing function is called.

        :param interval: Interval value for timing functions, in seconds.
        """
        self.interval = interval
        self.t_start = None
        self.ticks = 0
        self.restart()

    def _check(self):
        """
        Get the interval value for timing functions and initialize the time
        reference if not set yet.
        """
        if self.t_start is None:
            self.restart()
            self.t_start = perf_counter()

    def restart(self):
        """
        Reset the instance deleting its time reference, which will be set the
        next time a timing function is called.
        """
        self.t_start = None
        self.ticks = 0

    def elapsed(self, auto_reset=True, exact=True):
        """
        Checks if the interval has elapsed.

        :param auto_reset: If True, the time reference will be updated if the
                           the interval has elapsed.
        :param exact:      If True, the time reference will be increased with
                           the interval value, which will result in
                           deterministic and accurate intervals.
                           If False, the time reference will be updated to the
                           current time.
                           `exact` has no effect if `auto_reset` is False.
        :return:           True if the interval has elapsed, otherwise False.
        """
        self._check()
        ret = (perf_counter() - self.t_start >= self.interval)
        if ret and auto_reset:
            self.ticks += 1
            if exact:
                self.t_start += self.interval
            else:
                self.t_start = perf_counter()
        return ret

    def wait_next(self):
        """
        Blocks until the end of the current interval.
        Note that this function can return immediately if the next interval
        to wait has already elapsed. This happens when reusing a
        :class:`Throttle` instance without calling :func:`restart` first.
        """
        self._check()
        t_target = (self.t_start + self.interval)
        self.t_start += self.interval
        sleep_time = t_target - perf_counter()
        if sleep_time > 0:
            sleep(sleep_time)
        self.ticks += 1

    async def await_next(self):
        """
        Waits asynchronously until the end of the current interval.
        Note that this function can return immediately if the next interval
        to wait has already elapsed. This happens when reusing a
        :class:`Throttle` instance without calling :func:`restart` first.
        """
        self._check()
        t_target = (self.t_start + self.interval)
        self.t_start += self.interval
        await asyncio.sleep(t_target - perf_counter())
        self.ticks += 1

    def loop(self, max_ticks=None, duration=None):
        """
        Returns a synchronous generator yielding every time an interval has
        elapsed.

        You can specify a maximum number of iterations or a maximum duration
        for the generator, but not both. If none is set, the generator will
        run until you call break, return or raise an exception.

        :param max_ticks: Maximum number of intervals the generator will
                          wait for.
        :param duration:  Seconds of loop duration. The generator will loop
                          for ``ceil(duration / self.interval)`` iterations,
                          so the elapsed time may be longer than `duration`,
                          but never shorter.
        :return:          Yields the number of intervals elapsed since the
                          function was called.
        """
        max_ticks = self._check_loop_params(duration, max_ticks)
        ticks = 0

        while max_ticks is None or ticks < max_ticks:
            self.wait_next()
            yield ticks
            ticks += 1

    async def aloop(self, max_ticks=None, duration=None):
        """
        Returns an asynchronous generator yielding every time an interval has
        elapsed.

        You can specify a maximum number of iterations or a maximum duration
        for the generator, but not both. If none is set, the generator will
        run until you call break, return or raise an exception.

        :param max_ticks: Maximum number of intervals the generator will
                          wait for.
        :param duration:  Seconds of loop duration. The generator will loop
                          for ``ceil(duration / self.interval)`` iterations,
                          so the elapsed time may be longer than `duration`,
                          but never shorter.
        :return:          Yields the number of intervals elapsed since the
                          function was called.
        """
        max_ticks = self._check_loop_params(duration, max_ticks)
        ticks = 0

        while max_ticks is None or ticks < max_ticks:
            await self.await_next()
            yield ticks
            ticks += 1

    def _check_loop_params(self, duration, max_ticks):
        """
        Helper function for :func:`loop` and :func:`aloop`.
        """
        if max_ticks is not None and duration is not None:
            raise ValueError("max_ticks and duration cannot be set at"
                             "the same time")
        self._check()

        if duration is not None:
            max_ticks = math.ceil(duration / self.interval)

        return max_ticks


def throttle(limit=1, interval=1.0, wait=False, on_fail=None):
    """
    Decorator to limit the number of calls to a synchronous function in
    an interval of time. It ensures that the decorated function is not
    called more than `limit` times in the same time interval.
    If limit is reached, it can return a custom result or sleep until
    the next time interval.
    Do not use this function to decorate an asynchronous function (use
    :func:`~throttle.athrottle` instead).

    :param limit:    Maximum number of calls allowed to the decorated
                     function in each time interval.
    :param interval: Seconds of every time period.
    :param wait:     If True, it will block when limit is reached until
                     the next interval, and then it will call the function.
    :param on_fail:  Value, object or function to return if the call
                     limit is reached. If `on_fail` is a function, the
                     decorator will return the result of the call to
                     this function. Note that `on_fail` only makes sense
                     if `wait` is False.
    :return:         Result of the call to the decorated function, or
                     `on_fail` if limit is reached (and `wait` is False).
    """
    call_counter = 0
    throttle_ = Throttle(interval)

    def decorator(func):

        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal call_counter
            call_counter += 1

            if throttle_.elapsed():
                call_counter = 1
            elif call_counter > limit:
                if wait:
                    throttle_.wait_next()
                    call_counter = 1
                else:
                    return on_fail() if callable(on_fail) else on_fail

            return func(*args, **kwargs)

        return wrapper

    return decorator


def athrottle(limit=1, interval=1.0, wait=False, on_fail=None):
    """
    Decorator to limit the number of calls to a synchronous or asynchronous
    function in an interval of time. It ensures that the decorated function
    is not called more than `limit` times in the same time interval.
    If limit is reached, it can return a custom result or sleep until
    the next time interval.
    Do not use this function to decorate a synchronous function (use
    :func:`~throttle.throttle` instead).

    :param limit:    Maximum number of calls allowed to the decorated
                     function in each time interval.
    :param interval: Seconds of every time period.
    :param wait:     If True, it will asynchronously wait when limit is
                     reached until the next interval, and then it will
                     call the function.
    :param on_fail:  Value, object or function to return if the call
                     limit is reached. If `on_fail` is a function, the
                     decorator will return the result of the call to
                     this function (if this function is asynchronous,
                     it will await for its result). Note that `on_fail`
                     only makes sense if `wait` is False.
    :return:         Result of the call to the decorated function, or
                     `on_fail` if limit is reached (and `wait` is False).
    """
    call_counter = 0
    throttle_ = Throttle(interval)

    def decorator(func):

        @wraps(func)
        async def awrapper(*args, **kwargs):
            nonlocal call_counter
            call_counter += 1

            if throttle_.elapsed():
                call_counter = 1
            elif call_counter > limit:
                if wait:
                    await throttle_.await_next()
                    call_counter = 1
                else:
                    if inspect.iscoroutinefunction(on_fail):
                        return await on_fail()
                    elif inspect.isfunction(on_fail):
                        return on_fail()
                    else:
                        return on_fail

            if inspect.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)

        return awrapper

    return decorator
