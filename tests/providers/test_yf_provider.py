import pytest
import pandas as pd
from unittest.mock import patch

from trdr.core.data.providers.yf_provider import YFProvider
from trdr.core.data.interfaces import DataProviderError
from stonks_shared.enums.timeframe import Timeframe
from trdr.core.data.models import Bar
from trdr.core.money.money import Money

@pytest.fixture
def sample_yf_data():
    # Create a sample DataFrame with MultiIndex columns similar to yf.download output
    dates = pd.date_range(start='2024-01-01', end='2024-01-05')
    data = {
        'Open': [150.0] * 5,
        'High': [155.0] * 5,
        'Low': [145.0] * 5,
        'Close': [152.0] * 5,
        'Volume': [1000000] * 5,
    }
    df = pd.DataFrame(data, index=dates)
    
    # Create the MultiIndex structure that yfinance returns
    df.columns = pd.MultiIndex.from_product([['AAPL'], df.columns])
    return df

@pytest.mark.asyncio
async def test_initialization():
    symbols = ["AAPL", "MSFT"]
    provider = YFProvider(symbols)
    assert provider._symbols == set(symbols)
    assert provider._timeframe == Timeframe.D1
    assert not provider._initialized

@pytest.mark.asyncio
async def test_initialization_too_many_symbols():
    symbols = ["AAPL"] * 601
    with pytest.raises(DataProviderError, match="Yahoo Finance Provider does not support more than 600 symbols"):
        YFProvider(symbols)

@pytest.mark.asyncio
async def test_provider_create(sample_yf_data):
    with patch('yfinance.download', return_value=sample_yf_data):
        provider = await YFProvider.create(["AAPL"])
        assert provider._initialized
        assert "AAPL" in provider._data_cache
        assert len(provider._data_cache["AAPL"]) == 5

@pytest.mark.asyncio
async def test_get_bars(sample_yf_data):
    with patch('yfinance.download', return_value=sample_yf_data):
        provider = await YFProvider.create(["AAPL"])
        bars = await provider.get_bars("AAPL", 3)
        
        assert len(bars) == 3
        assert isinstance(bars[0], Bar)
        assert bars[0].open == Money(150.0)
        assert bars[0].high == Money(155.0)
        assert bars[0].low == Money(145.0)
        assert bars[0].close == Money(152.0)
        assert bars[0].volume == 1000000

@pytest.mark.asyncio
async def test_get_bars_invalid_symbol():
    empty_df = pd.DataFrame(columns=pd.MultiIndex.from_product([['AAPL'], ['Open', 'High', 'Low', 'Close', 'Volume']]))
    with patch('yfinance.download', return_value=empty_df):
        provider = await YFProvider.create(["AAPL"])
        with pytest.raises(DataProviderError, match="No data found for symbol: INVALID"):
            await provider.get_bars("INVALID", 3)

@pytest.mark.asyncio
async def test_get_bars_invalid_lookback(sample_yf_data):
    with patch('yfinance.download', return_value=sample_yf_data):
        provider = await YFProvider.create(["AAPL"])
        with pytest.raises(DataProviderError, match="Not enough data to fetch 10 bars"):
            await provider.get_bars("AAPL", 10)

@pytest.mark.asyncio
async def test_fetch_batch_stock_data_failure():
    with patch('yfinance.download', side_effect=Exception("API Error")):
        provider = YFProvider(["AAPL"])
        with pytest.raises(DataProviderError, match="Error fetching data from Yahoo Finance"):
            await provider._fetch_batch_stock_data(["AAPL"])