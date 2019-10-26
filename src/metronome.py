import asyncio
from time import perf_counter


class Metronome:
    def __init__(self, interval=None, auto_reset=True, exact=False):
        self.interval = interval
        self.auto_reset = auto_reset
        self.exact = exact
        self.t_start = perf_counter()
        self.timer = None
        self.available = 0
        self.ticks = 0
        self.started = False
        self.start()

    def _get_interval(self, interval=None):
        interval = interval if interval else self.interval
        if not interval:
            raise Exception("interval not defined")
        return interval

    def start(self):
        self.t_start = perf_counter()
        self.ticks = 0
        self.started = True

    def elapsed(self, seconds=None):
        seconds = self._get_interval(seconds)
        ret = (perf_counter() - self.t_start >= seconds)
        if ret and self.auto_reset:
            if self.exact:
                self.t_start += seconds
            else:
                self.t_start = perf_counter()
        return ret

    async def wait_until_available(self, seconds=None):
        seconds = self._get_interval(seconds)
        t_target = (self.t_start + seconds)
        self.t_start += seconds
        await asyncio.sleep(t_target - perf_counter())
        self.ticks += 1
