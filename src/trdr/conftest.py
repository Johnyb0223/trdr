import asyncio
import datetime
import pandas as pd
import pytest
import yfinance as yf

from .core.security_provider.security_provider import SecurityProvider
from .core.bar_provider.yf_bar_provider.yf_bar_provider import YFBarProvider


def fake_yf_download(*args, **kwargs):
    """
    This returns fake batch stock data for two symbols. This is what yahoo finance returns for a batch download request
    grouped by symbol over a 3 day period.
    """
    dates = pd.bdate_range(end=datetime.datetime.now(), periods=3)

    data = {
        ("AAPL", "Open"): [100, 101, 102],
        ("AAPL", "High"): [110, 111, 112],
        ("AAPL", "Low"): [90, 91, 92],
        ("AAPL", "Close"): [105, 106, 107],
        ("AAPL", "Volume"): [1000, 1100, 1200],
        ("MSFT", "Open"): [200, 201, 202],
        ("MSFT", "High"): [210, 211, 212],
        ("MSFT", "Low"): [190, 191, 192],
        ("MSFT", "Close"): [205, 206, 207],
        ("MSFT", "Volume"): [2000, 2100, 2200],
        # this is what is returned when a symbol is not found
        ("ABCDEFG", "Open"): [None, None, None],
        ("ABCDEFG", "High"): [None, None, None],
        ("ABCDEFG", "Low"): [None, None, None],
        ("ABCDEFG", "Close"): [None, None, None],
        ("ABCDEFG", "Volume"): [None, None, None],
        # this is what is returned when we hit the rate limit
        ("AMZN", "Open"): None,
        ("AMZN", "High"): None,
        ("AMZN", "Low"): None,
        ("AMZN", "Close"): None,
        ("AMZN", "Volume"): None,
    }

    return pd.DataFrame(data, index=dates)


@pytest.fixture(scope="function")
def yf_bar_provider_with_fake_data(monkeypatch):
    monkeypatch.setattr(yf, "download", fake_yf_download)
    monkeypatch.setattr(yf.shared, "_ERRORS", {"ABCDEFG": "YFTzMissingError()", "AMZN": "JSONDecodeError()"})
    return asyncio.run(YFBarProvider.create(["AAPL", "MSFT", "ABCDEFG", "AMZN"]))


@pytest.fixture(scope="function")
def security_provider_with_fake_data(yf_bar_provider_with_fake_data):
    return asyncio.run(SecurityProvider.create(yf_bar_provider_with_fake_data))
