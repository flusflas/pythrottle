import asyncio
from time import perf_counter


class Metronome:
    def __init__(self, interval=None, auto_reset=True, exact=False, loop=None):
        self.interval = interval
        self.auto_reset = auto_reset
        self.exact = exact
        self.t_start = perf_counter()
        self.t_next = 0
        self.timer = None
        self.available = 0
        self.ticks = 0
        self.sem = asyncio.Semaphore(value=1, loop=loop)
        self.started = False
        self.start()

    def _get_interval(self, interval=None):
        interval = interval if interval else self.interval
        if not interval:
            raise Exception("interval not defined")
        return interval

    def start(self):
        self.t_start = perf_counter()
        self.t_next = self.t_start
        self.ticks = 0
        self.started = True

    def elapsed(self, seconds=None):
        seconds = self._get_interval(seconds)
        ret = (perf_counter() - self.t_next >= seconds)
        if ret and self.auto_reset:
            if self.exact:
                self.t_next += seconds
            else:
                self.t_next = perf_counter()
        return ret

    async def wait_until_available(self, seconds=None):
        seconds = self._get_interval(seconds)
        async with self.sem:    # TODO: Semaphore seems not necessary...
            self.ticks += 1
            await asyncio.sleep((self.t_start + self.ticks * seconds) - perf_counter())
