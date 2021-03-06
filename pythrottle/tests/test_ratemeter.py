import pytest

from pythrottle.rate_meter import RateMeter
from pythrottle.throttle import Throttle


RATE = 1000
INTERVAL = 2.0
MAX_ERROR = 0.01 / 100


@pytest.fixture(name="throttle")
def throttle_fxt():
    """
    Yields a :class:`Throttle` instance with the default rate.
    """
    yield Throttle(interval=(1 / RATE))


@pytest.fixture(name="rate_meter")
def rate_meter_fxt():
    return RateMeter(interval=INTERVAL)


def assert_results(rate_meter, values):
    mean = sum(values) / len(values)
    assert abs(1 - mean / RATE) < MAX_ERROR
    assert abs(1 - rate_meter.rate() / RATE) < MAX_ERROR

    rate_meter.restart()
    assert rate_meter.rate() == 0
    assert len(rate_meter._iters) == 0
    assert len(rate_meter._times) == 0


def test_ratemeter_non_consecutive_update(throttle, rate_meter):
    """
    Tests the measurement of the rate of an iterative code using
    `update()` in non-consecutive iterations.
    """
    iters = 5 * RATE
    values = []

    assert rate_meter.rate() == 0

    for i in throttle.loop(iters):
        if i % 5 == 0:
            rate_meter.update(i)
        measured_rate = rate_meter.rate()
        if i > measured_rate != 0:
            values.append(measured_rate)

    assert_results(rate_meter, values)


def test_ratemeter_default_update_param(throttle, rate_meter):
    """
    Tests the measurement of the rate of an iterative code using
    `update()` with default parameter in each iteration.
    """
    iters = 5 * RATE
    values = []

    assert rate_meter.rate() == 0

    for i in throttle.loop(iters):
        rate_meter.update()
        measured_rate = rate_meter.rate()
        if i > measured_rate != 0:
            values.append(measured_rate)

    assert_results(rate_meter, values)
