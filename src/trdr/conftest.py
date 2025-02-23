import asyncio
import pytest
import yfinance as yf

from .core.security_provider.security_provider import SecurityProvider
from .core.bar_provider.yf_bar_provider.yf_bar_provider import YFBarProvider
from .core.shared.models import Timeframe
from .utils.fake_yf_download import fake_yf_download
from .utils.security_generator import SecurityGenerator, Criteria, Crossover


@pytest.fixture(scope="function")
def yf_bar_provider_with_fake_data(monkeypatch):
    monkeypatch.setattr(yf, "download", fake_yf_download)
    monkeypatch.setattr(yf.shared, "_ERRORS", {"ABCDEFG": "YFTzMissingError()", "AMZN": "JSONDecodeError()"})
    return asyncio.run(YFBarProvider.create(["AAPL", "MSFT", "ABCDEFG", "AMZN"]))


@pytest.fixture(scope="function")
def security_provider_with_fake_data(yf_bar_provider_with_fake_data):
    return asyncio.run(SecurityProvider.create(yf_bar_provider_with_fake_data))


@pytest.fixture(scope="function")
def get_random_security():
    generator = SecurityGenerator(Criteria(count=200))
    return generator.find_suitable_security()


@pytest.fixture(scope="module")
def get_security_generator():
    return SecurityGenerator(Criteria(count=200))
