import time


class Profiler:
    """
    This class can be used as a context manager to time a block of code and
    calculate some metrics.
    """

    def __init__(self, iter_count=0, target_rate=None):
        self.t_start = 0.0
        self.t_end = 0.0
        self.iter_count = iter_count
        self.target_rate = target_rate

    @property
    def elapsed(self):
        return self.t_end - self.t_start

    @property
    def measured_rate(self):
        return self.iter_count / self.elapsed

    @property
    def error(self):
        return 1 - self.measured_rate / self.target_rate

    def __enter__(self):
        self.t_start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.t_end = time.perf_counter()
