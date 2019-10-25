import asyncio
from time import perf_counter

import uvloop

from src.metronome import Metronome


met = None      # type: Metronome
rate = 1000

t_init = 0
sem = asyncio.Semaphore()


async def test_interval(i):
    await met.wait_until_available()
    # et.sleep_until_ready(1 / rate)
    # print(f"{i} - {perf_counter()}")

    # async with sem:
    #     # print(i)
    #     p = perf_counter()
    #     wait_until = (t_init + (i+1)*(1 / rate)) - p
    #     await asyncio.sleep(wait_until)


async def main():
    global sem, t_init, met
    sem = asyncio.Semaphore()
    met = Metronome(1 / rate)

    iter_count = 5000

    met.start()
    t_init = perf_counter()
    t_start = perf_counter()
    await asyncio.gather(*(test_interval(i) for i in range(iter_count)))
    t_end = perf_counter()
    print(f"Rate: {iter_count / (t_end - t_start)}")

    print("------------------------")
    await asyncio.sleep(5)

    met.start()
    t_start = perf_counter()
    await asyncio.gather(*(test_interval(i) for i in range(iter_count)))
    t_end = perf_counter()
    print(f"Rate: {iter_count / (t_end - t_start)}")


if __name__ == '__main__':
    uvloop.install()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
