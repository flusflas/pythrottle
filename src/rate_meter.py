from bisect import bisect_left
from collections import deque
from time import perf_counter


class RateMeter:
    def __init__(self, interval=1.0):
        self._times = deque()
        self._values = deque()
        self.interval = interval

    def restart(self):
        self._times.clear()
        self._values.clear()

    def _remove_past_items(self):
        first_time_value = self._times[-1] - self.interval
        first_time_index = bisect_left(self._times, first_time_value)

        # Time difference between last and first items must remain
        # equal or greater than 'interval'
        if self._times.count(first_time_value) == 0:
            first_time_index -= 1

        for _ in range(first_time_index):
            self._times.popleft()
            self._values.popleft()

    def update(self, value):
        t_current = perf_counter()
        self._times.append(t_current)
        self._values.append(value)
        self._remove_past_items()

    def rate(self):
        if len(self._times) <= 1:
            return 0

        value_diff = self._values[-1] - self._values[0]
        time_diff = self._times[-1] - self._times[0]
        return 0 if time_diff == 0 else value_diff / time_diff
