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
        self.condition = asyncio.Condition(loop=loop)
        self.started = False
        self.start()

    async def periodic(self, interval=None):
        interval = interval if interval else self.interval
        while self.started:
            await asyncio.sleep((self.t_start + (self.ticks+1)*interval) - perf_counter())
            await self._callback()

    def start(self, interval=None):
        interval = interval if interval else self.interval
        self.started = True
        asyncio.get_running_loop().create_task(self.periodic(interval))

    async def _callback(self):
        async with self.condition:
            self.condition.notify(1)
        self.available += 1
        self.ticks += 1

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

        async with self.condition:
            await self.condition.wait()
