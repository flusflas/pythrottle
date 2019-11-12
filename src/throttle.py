import asyncio
import inspect
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
    >>> i_start = perf_counter()
    >>> for i in throttle.sleep_loop(24):
    ...     # Take, process and save image
    ...     iters += 1
    >>> total_time = round(perf_counter() - i_start, 2)
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

    def sleep_until_available(self):
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

    async def wait_until_available(self):
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

    def sleep_loop(self, max_ticks=None):
        """
        Returns a synchronous generator yielding every time an interval has
        elapsed.

        :param max_ticks: Maximum number of intervals the generator will
                          wait for. If not set, it will run until you call
                          break or return.
        :return:          Yields the number of intervals elapsed since the
                          function was called.
        """
        self._check()
        ticks = 0
        while max_ticks is None or ticks < max_ticks:
            if max_ticks:
                ticks += 1
            self.sleep_until_available()
            yield ticks

    async def wait_loop(self, max_ticks=None):
        """
        Returns an asynchronous generator yielding every time an interval has
        elapsed.

        :param max_ticks: Maximum number of intervals the generator will
                          wait for. If not set, it will run until `break`
                          or `return` is called.
        :return:          Yields the number of intervals elapsed since the
                          function was called.
        """
        self._check()
        ticks = 0
        while max_ticks is None or ticks < max_ticks:
            if max_ticks:
                ticks += 1
            await self.wait_until_available()
            yield ticks


def throttle(limit, interval, wait=False, on_fail=None):
    """
    Decorator to limit the number of calls to a synchronous function in
    an interval of time. It ensures that the decorated function is not
    called more than `limit` times in the same time interval.
    If limit is reached, it can return a custom result or sleep until
    the next time interval.
    Do not use this function to decorate an asynchronous function (use
    :func:`athrottle` instead).

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
    throttle = Throttle(interval)

    def decorator(func):

        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal call_counter
            call_counter += 1

            if throttle.elapsed():
                call_counter = 1
            elif call_counter > limit:
                if wait:
                    throttle.sleep_until_available()
                    call_counter = 1
                else:
                    return on_fail() if callable(on_fail) else on_fail

            return func(*args, **kwargs)

        return wrapper

    return decorator


def athrottle(limit, interval, wait=False, on_fail=None):
    """
    Decorator to limit the number of calls to a synchronous or
    asynchronous function in an interval of time. It ensures that the
    decorated function is not called more than `limit` times in the
    same time interval.
    If limit is reached, it can return a custom result or sleep until
    the next time interval.
    Do not use this function to decorate a synchronous function (use
    :func:`throttle` instead).

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
    throttle = Throttle(interval)

    def decorator(func):

        @wraps(func)
        async def awrapper(*args, **kwargs):
            nonlocal call_counter
            call_counter += 1

            if throttle.elapsed():
                call_counter = 1
            elif call_counter > limit:
                if wait:
                    await throttle.wait_until_available()
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
