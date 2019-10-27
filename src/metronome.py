import asyncio
from time import perf_counter, sleep


class Metronome:
    def __init__(self, interval=None):
        self.interval = interval
        self.t_start = perf_counter()
        self.ticks = 0
        self.started = False
        self.start()

    def _get_interval(self, interval=None):
        interval = interval if interval else self.interval
        if not interval:
            raise ValueError("interval not defined")
        return interval

    def start(self):
        self.t_start = perf_counter()
        self.ticks = 0
        self.started = True

    def elapsed(self, seconds=None, auto_reset=True, exact=True):
        seconds = self._get_interval(seconds)
        ret = (perf_counter() - self.t_start >= seconds)
        if ret and auto_reset:
            self.ticks += 1
            if exact:
                self.t_start += seconds
            else:
                self.t_start = perf_counter()
        return ret

    def sleep_until_available(self, seconds=None):
        seconds = self._get_interval(seconds)
        t_target = (self.t_start + seconds)
        self.t_start += seconds
        sleep_time = t_target - perf_counter()
        if sleep_time > 0:
            sleep(sleep_time)
        self.ticks += 1

    async def wait_until_available(self, seconds=None):
        seconds = self._get_interval(seconds)
        t_target = (self.t_start + seconds)
        self.t_start += seconds
        await asyncio.sleep(t_target - perf_counter())
        self.ticks += 1

    def sleep_loop(self, seconds=None, max_ticks=None):
        seconds = self._get_interval(seconds)
        ticks = 0
        while max_ticks is None or ticks < max_ticks:
            if max_ticks:
                ticks += 1
            self.sleep_until_available(seconds)
            yield ticks

    async def wait_loop(self, seconds=None, max_ticks=None):
        seconds = self._get_interval(seconds)
        ticks = 0
        while max_ticks is None or ticks < max_ticks:
            if max_ticks:
                ticks += 1
            await self.wait_until_available(seconds)
            yield ticks
