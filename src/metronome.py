import asyncio
from time import perf_counter, sleep


class Metronome:
    """
    This class offers mechanisms to rate-limit the execution of some
    iterative code.

    Example:
    >>> rate = 24   # fps
    >>> metronome = Metronome(interval=(1 / rate))
    >>> iters = 0
    >>> i_start = perf_counter()
    >>> for i in metronome.sleep_loop(24):
    ...     # Take, process and save image
    ...     iters += 1
    >>> total_time = round(perf_counter() - i_start, 2)
    >>> print('iters: {}, total_time: {}'.format(iters, total_time))
    iters: 24, total_time: 1.0
    """

    def __init__(self, interval):
        """
        Returns a :class:`Metronome` instance. Time reference will be set the
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
        :class:`Metronome` instance without calling :func:`restart` first.
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
        :class:`Metronome` instance without calling :func:`restart` first.
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
