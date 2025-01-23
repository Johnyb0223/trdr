from typing import List, Optional
from datetime import datetime, timedelta, timezone
import yfinance as yf
import pandas as pd
import asyncio

from trdr.core.data.interfaces import DataProviderError
from trdr.core.data.models import Bar
from trdr.core.time.trading_datetime import TradingDateTime
from stonks_shared.enums.timeframe import Timeframe
from trdr.core.data.base_data_provider import BaseDataProvider
from trdr.core.money.money import Money

class YFProvider(BaseDataProvider):
    def __init__(self, symbols: List[str], timeframe: Timeframe = Timeframe.D1):
        if len(symbols) > 600:
            raise DataProviderError("Yahoo Finance Provider does not support more than 600 symbols")
        super().__init__(symbols, timeframe)
        
    async def _initialize(self) -> None:
        '''
        this function is called by the factory method in the base class upon instantiation
        of a new provider.
        '''
        data = await self._fetch_batch_stock_data(list(self._symbols))
        for symbol in self._symbols:
            symbol_data = data.xs(symbol, level=0, axis=1)
            bars = self._convert_df_to_bars(symbol_data)
            self._data_cache[symbol] = bars
        self._initialized = True

    async def _fetch_batch_stock_data(
        self,
        tickers: List[str],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        '''
        raises DataProviderError on failure to fetch data from Yahoo Finance
        '''
        
        end_date = end_date or datetime.today().date()
        start_date = start_date or (end_date - timedelta(days=300))
        
        try:
            data = yf.download(tickers, start=start_date, end=end_date, group_by='ticker')
        except Exception as e:
            raise DataProviderError(f"Error fetching data from Yahoo Finance: {e}")
        
        return data
    
    def _convert_df_to_bars(self, df: pd.DataFrame) -> List[Bar]:

        bars = []
        
        for date, row in df.iterrows():
            try:
                utc_timestamp = pd.Timestamp(date).to_pydatetime().replace(tzinfo=timezone.utc)
                bar = Bar(
                    trading_datetime=TradingDateTime.from_utc(utc_timestamp),
                    timeframe=self._timeframe,
                    open=Money(row['Open']),
                    high=Money(row['High']),
                    low=Money(row['Low']),
                    close=Money(row['Close']),
                    volume=int(row['Volume'])
                )
                bars.append(bar)
            except Exception as e:
                print(f"Error converting bar for date {date}: {e}")
        
        return bars

    async def get_bars(
        self,
        symbol: str,
        lookback: int,
    ) -> List[Bar]:
        '''
        returns a list of bars of len(lookback) from oldest to newest
        raises DataProviderError if the provider is not initialized, if the symbol is not supported, or if there is not enough data to fetch the requested lookback
        '''
        if not self._initialized:
            raise DataProviderError("DataProvider not initialized")
        if symbol not in self._data_cache:
            raise DataProviderError(f"No data found for symbol: {symbol}")
        if lookback > len(self._data_cache[symbol]):
            raise DataProviderError(f"Not enough data to fetch {lookback} bars for symbol: {symbol}")

        bars = []
        start_index = len(self._data_cache[symbol]) - lookback
        for i in range(start_index, len(self._data_cache[symbol])):
            bars.append(self._data_cache[symbol][i])
        return bars
    
if __name__ == "__main__":
    async def main():
        provider = await YFProvider.create(["AAPL", "MSFT", "GOOGL"])
        appl_bars = await provider.get_bars("AAPL", 10)
        for bar in appl_bars:
            print(bar)
    
    asyncio.run(main())