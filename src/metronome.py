import asyncio
from time import perf_counter, sleep


class Metronome:
    """

    """

    def __init__(self, interval=None):
        """
        Returns a :class:`Metronome` instance. Time reference will be set the
        first time a timing function is called.

        :param interval: Default interval value for timing functions, in
                         seconds. If not set, timing functions must specify
                         an interval value.
        """
        self.interval = interval
        self.t_start = None
        self.ticks = 0
        self.restart()

    def _get_interval_and_check(self, interval=None):
        """
        Get the interval value for timing functions and initialize the time
        reference if not set yet.

        :param interval: Interval value for timing functions. If not set,
                         default interval value will be used. If none of them
                         are set, a ValueError will be raised.
        :return:         Interval value.
        """
        interval = interval if interval else self.interval
        if not interval:
            raise ValueError("interval not defined")
        if self.t_start is None:
            self.restart()
            self.t_start = perf_counter()
        return interval

    def restart(self):
        """
        Reset the instance deleting its time reference, which will be set the
        next time a timing function is called.
        """
        self.t_start = None
        self.ticks = 0

    def elapsed(self, seconds=None, auto_reset=True, exact=True):
        """
        Checks if the interval has elapsed.

        :param seconds:     Number of seconds for the current interval. If not
                            set, default interval will be used.
        :param auto_reset:  If True, the time reference will be updated if the
                            the interval has elapsed.
        :param exact:       If True, the time reference will be increased with
                            the interval value, which will result in
                            deterministic and accurate intervals.
                            If False, the time reference will be updated to the
                            current time.
        :return:            True if the interval has elapsed, otherwise False.
        """
        seconds = self._get_interval_and_check(seconds)
        ret = (perf_counter() - self.t_start >= seconds)
        if ret and auto_reset:
            self.ticks += 1
            if exact:
                self.t_start += seconds
            else:
                self.t_start = perf_counter()
        return ret

    def sleep_until_available(self, seconds=None):
        """
        Blocks until the end of the current interval.
        Note that this function can return immediately if the next interval to
        wait has already elapsed.

        :param seconds: Number of seconds for the current interval. If not
                        set, default interval will be used.
        """
        seconds = self._get_interval_and_check(seconds)
        t_target = (self.t_start + seconds)
        self.t_start += seconds
        sleep_time = t_target - perf_counter()
        if sleep_time > 0:
            sleep(sleep_time)
        self.ticks += 1

    async def wait_until_available(self, seconds=None):
        """
        Waits asynchronously until the end of the current interval.
        Note that this function can return immediately if the next interval to
        wait has already elapsed.

        :param seconds: Number of seconds for the current interval. If not
                        set, default interval will be used.
        """
        seconds = self._get_interval_and_check(seconds)
        t_target = (self.t_start + seconds)
        self.t_start += seconds
        await asyncio.sleep(t_target - perf_counter())
        self.ticks += 1

    def sleep_loop(self, seconds=None, max_ticks=None):
        """
        Returns a synchronous generator yielding every time an interval has
        elapsed.

        :param seconds:     Number of seconds for an interval. If not set,
                            default interval will be used.
        :param max_ticks:   Maximum number of intervals the generator will
                            wait for. If not set, it will run until you call
                            break or return.
        :return:            Yields the number of intervals elapsed since the
                            function was called.
        """
        seconds = self._get_interval_and_check(seconds)
        ticks = 0
        while max_ticks is None or ticks < max_ticks:
            if max_ticks:
                ticks += 1
            self.sleep_until_available(seconds)
            yield ticks

    async def wait_loop(self, seconds=None, max_ticks=None):
        """
        Returns an asynchronous generator yielding every time an interval has
        elapsed.

        :param seconds:     Number of seconds for an interval. If not set,
                            default interval will be used.
        :param max_ticks:   Maximum number of intervals the generator will
                            wait for. If not set, it will run until you call
                            break or return.
        :return:            Yields the number of intervals elapsed since the
                            function was called.
        """
        seconds = self._get_interval_and_check(seconds)
        ticks = 0
        while max_ticks is None or ticks < max_ticks:
            if max_ticks:
                ticks += 1
            await self.wait_until_available(seconds)
            yield ticks
