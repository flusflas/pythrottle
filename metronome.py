import asyncio
from time import perf_counter


class Metronome:
    def __init__(self, interval=None, loop=None):
        self.interval = interval
        self.t_start = perf_counter()
        self.timer = None
        self.available = 0
        self.ticks = 0
        self.sem = asyncio.Semaphore(value=1, loop=loop)
        self.started = False
        self.start()

    def start(self):
        self.t_start = perf_counter()
        self.ticks = 0
        self.started = True

    def elapsed(self, seconds=None):
        seconds = seconds if seconds else self.interval
        if not seconds:
            raise Exception("interval not defined")
        if self.available:
            self.available -= 1
            return True
        return False

    async def wait_until_available(self, seconds=None):
        seconds = seconds if seconds else self.interval
        async with self.sem:
            self.ticks += 1
            await asyncio.sleep((self.t_start + self.ticks * seconds) - perf_counter())
