import pytest

from ..security_provider.models import Timeframe
from ...test_utils.security_generator import SecurityCriteria, Crossover


def test_compute_average_volume(get_random_security):
    security = get_random_security
    d5_average_volume = sum(bar.volume for bar in security.bars[-5:]) // 5
    d20_average_volume = sum(bar.volume for bar in security.bars[-20:]) // 20
    assert security.compute_average_volume(Timeframe.d5) == d5_average_volume
    assert security.compute_average_volume(Timeframe.d20) == d20_average_volume


def test_compute_moving_average(get_random_security):
    security = get_random_security
    d5_moving_average = sum(bar.close.amount for bar in security.bars[-5:]) / 5
    assert security.compute_moving_average(Timeframe.d5).amount == d5_moving_average


def test_get_current_price_and_volume(get_random_security):
    security = get_random_security
    assert security.get_current_price() == security.current_bar.close
    assert security.get_current_volume() == security.current_bar.volume


def test_invalid_timeframe(get_random_security):
    security = get_random_security
    with pytest.raises(ValueError):
        security.compute_average_volume(None)
    with pytest.raises(ValueError):
        security.compute_moving_average(None)


def test_bullish_crossover(security_generator):
    crossover = Crossover(type="golden_cross", ma1=Timeframe.d5, ma2=Timeframe.d20)
    criteria = SecurityCriteria(count=200, crossovers=[crossover])
    generator = security_generator
    generator.criteria = criteria
    security = generator.find_suitable_security()
    result = security.has_bullish_moving_average_crossover(Timeframe.d5, Timeframe.d20)
    assert result is True


def test_bearish_crossover(security_generator):
    crossover = Crossover(type="death_cross", ma1=Timeframe.d5, ma2=Timeframe.d20)
    criteria = SecurityCriteria(count=200, crossovers=[crossover])
    generator = security_generator
    generator.criteria = criteria
    security = generator.find_suitable_security()
    result = security.has_bearish_moving_average_crossover(Timeframe.d5, Timeframe.d20)
    assert result is True


def test_compute_average_volume_with_offset(get_random_security):
    security = get_random_security

    large_offset = len(security.bars) - 2
    assert security.compute_average_volume(Timeframe.d5, offset=large_offset) is None
    assert security.compute_average_volume(Timeframe.d5, offset=len(security.bars)) is None


def test_compute_moving_average_with_offset(get_random_security):
    security = get_random_security
    large_offset = len(security.bars) - 2
    assert security.compute_moving_average(Timeframe.d5, offset=large_offset) is None
    assert security.compute_moving_average(Timeframe.d5, offset=len(security.bars)) is None


def test_compute_average_volume_zero_days(get_random_security):
    security = get_random_security

    with pytest.raises(ValueError):
        security.compute_average_volume(Timeframe.m15)
