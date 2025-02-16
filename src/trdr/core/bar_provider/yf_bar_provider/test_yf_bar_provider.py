import pytest
import pandas as pd
import datetime
import asyncio
import yfinance as yf

from trdr.core.bar_provider.yf_bar_provider.yf_bar_provider import YFBarProvider
from trdr.core.bar_provider.exceptions import NoBarsForSymbolException, BarProviderException, InsufficientBarsException


def fake_yf_download(self, start, end, group_by, interval):
    """
    This return fake batch stock data for two symbols. This is what yahoo finance returns for a batch download request
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
        ("ABCDEFG", "Open"): [None, None, None],
        ("ABCDEFG", "High"): [None, None, None],
        ("ABCDEFG", "Low"): [None, None, None],
        ("ABCDEFG", "Close"): [None, None, None],
        ("ABCDEFG", "Volume"): [None, None, None],
    }

    return pd.DataFrame(data, index=dates)


@pytest.fixture(scope="function")
def yf_bar_provider_with_fake_data(monkeypatch):
    monkeypatch.setattr(yf, "download", fake_yf_download)
    monkeypatch.setattr(yf.shared, "_ERRORS", {"ABCDEFG": "YFTzMissingError()"})
    return asyncio.run(YFBarProvider.create(["AAPL", "MSFT", "ABCDEFG"]))


def test_get_symbols_returns_a_list_of_symbols(yf_bar_provider_with_fake_data):
    expected_symbols = {"AAPL", "MSFT"}
    actual_symbols = set(yf_bar_provider_with_fake_data.get_symbols())
    assert actual_symbols == expected_symbols


def test_get_symbols_returns_only_symbols_that_have_bars(yf_bar_provider_with_fake_data):
    expected_symbols = {"AAPL", "MSFT"}
    actual_symbols = set(yf_bar_provider_with_fake_data.get_symbols())
    assert actual_symbols == expected_symbols


def test_gets_bars_throws_exception_when_no_bars_are_available_for_a_symbol(yf_bar_provider_with_fake_data):
    with pytest.raises(NoBarsForSymbolException):
        bars = asyncio.run(yf_bar_provider_with_fake_data.get_bars("ABCDEFG", 200))


def test_provider_throws_exception_when_data_source_returns_error(monkeypatch):
    with pytest.raises(BarProviderException):
        monkeypatch.setattr(yf, "download", fake_yf_download)
        monkeypatch.setattr(yf.shared, "_ERRORS", {"ABCDEFG": "RandomYFError()"})
        bars = asyncio.run(YFBarProvider.create(["ABCDEFG"]))


def test_get_bars_throws_exception_when_symbol_is_not_in_data_cache(yf_bar_provider_with_fake_data):
    with pytest.raises(NoBarsForSymbolException):
        bars = asyncio.run(yf_bar_provider_with_fake_data.get_bars("ABCDEFG", 200))


def test_get_bars_throws_exception_when_lookback_is_greater_than_the_number_of_bars_available(
    yf_bar_provider_with_fake_data,
):
    with pytest.raises(InsufficientBarsException):
        bars = asyncio.run(yf_bar_provider_with_fake_data.get_bars("AAPL", 4))


def test_get_current_bar_throws_exception_when_no_bars_are_available_for_a_symbol(yf_bar_provider_with_fake_data):
    with pytest.raises(NoBarsForSymbolException):
        bar = asyncio.run(yf_bar_provider_with_fake_data.get_current_bar("ABCDEFG"))


def test_get_current_bar_throws_exception_when_data_source_returns_error(monkeypatch):
    with pytest.raises(BarProviderException):
        monkeypatch.setattr(yf, "download", fake_yf_download)
        yf_bar_provider = asyncio.run(YFBarProvider.create(["ABCDEFG"]))
        monkeypatch.setattr(yf.shared, "_ERRORS", {"ABCDEFG": "RandomYFError()"})
        bar = asyncio.run(yf_bar_provider.get_current_bar("ABCDEFG"))
