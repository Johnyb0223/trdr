from typing import List
from datetime import timedelta, timezone
import yfinance as yf
import pandas as pd
from opentelemetry import trace

from ..exceptions import (
    BarProviderException,
    InsufficientBarsException,
    DataSourceException,
    NoBarsForSymbolException,
)
from ..base_bar_provider import BaseBarProvider
from ..models import Bar, TradingDateTime, Money


class YFBarProvider(BaseBarProvider):
    def __init__(
        self,
        *args,
        **kwargs,
    ):
        """Disabled constructor - use YFBarProvider.create() instead."""
        raise TypeError("Use YFBarProvider.create() instead to create a new bar provider")

    async def _initialize(self) -> None:
        """
        this function is called by the T.create() method implemented in the base class. Use that method to create a new bar provider.
        """
        with self._tracer.start_as_current_span("YFBarProvider._initialize") as span:
            if not self._symbols:
                span.set_status(trace.Status(trace.StatusCode.ERROR))
                e = BarProviderException("Symbols must be provided")
                span.record_exception(e)
                raise e
            if len(self._symbols) > 600:
                span.set_status(trace.Status(trace.StatusCode.ERROR))
                e = BarProviderException("Yahoo Finance Provider does not support more than 600 symbols")
                span.record_exception(e)
                raise e
            try:
                await self._refresh_data()
            except Exception as e:
                span.add_event("refresh_data_error")
                span.set_status(trace.Status(trace.StatusCode.ERROR))
                raise
            else:
                span.set_status(trace.Status(trace.StatusCode.OK))

    async def _refresh_data(self) -> None:
        """
        This function is called by the factory method in the base class upon instantiation
        of a new provider.
        """
        with self._tracer.start_as_current_span("YFBarProvider._refresh_data") as span:
            try:
                data = await self._fetch_batch_stock_data()
            except Exception as e:
                span.add_event("data_fetch_error")
                span.set_status(trace.Status(trace.StatusCode.ERROR))
                e = BarProviderException(f"Error fetching data from Yahoo Finance: {e}")
                span.record_exception(e)
                raise e
            else:
                for symbol in self._symbols:
                    try:
                        symbol_data = data.xs(symbol, level=0, axis=1)
                        bars = self._convert_df_to_bars(symbol_data)
                        self._data_cache[symbol] = bars
                    except Exception as e:
                        span.set_status(trace.Status(trace.StatusCode.ERROR))
                        e = BarProviderException(f"Error converting data for symbol: {symbol} to bars")
                        span.record_exception(e)
                        raise e
                span.set_status(trace.Status(trace.StatusCode.OK))
                span.add_event("refresh_complete")

    async def _fetch_batch_stock_data(
        self,
    ) -> pd.DataFrame:

        with self._tracer.start_as_current_span("YFBarProvider._fetch_batch_stock_data") as span:

            end_datetime = TradingDateTime.now().timestamp
            start_datetime = end_datetime - timedelta(days=300)

            span.set_attribute("total_symbols_to_fetch_data_for", len(self._symbols))
            span.set_attribute("start_datetime", str(start_datetime))
            span.set_attribute("end_datetime", str(end_datetime))
            span.set_attribute("date_range_days", (end_datetime - start_datetime).days)
            span.add_event("begin_data_fetch")
            data = yf.download(
                self._symbols,
                start=start_datetime,
                end=end_datetime,
                group_by="ticker",
                interval="1d",
            )
            span.add_event("data_fetch_complete")
            if yf.shared._ERRORS:
                error_msg = "; ".join(yf.shared._ERRORS.values())
                span.set_status(trace.Status(trace.StatusCode.ERROR))
                e = BarProviderException(f"YFinance errors: {error_msg}")
                span.record_exception(e)
                raise e

            span.set_status(trace.Status(trace.StatusCode.OK))
            return data

    def _convert_df_to_bars(self, df: pd.DataFrame) -> List[Bar]:
        with self._tracer.start_as_current_span("YFBarProvider._convert_df_to_bars") as span:

            bars = []
            total_rows = len(df)
            accumulated_errors = []

            for date, row in df.iterrows():
                try:
                    utc_timestamp = pd.Timestamp(date).to_pydatetime().replace(tzinfo=timezone.utc)
                    bar = Bar(
                        trading_datetime=TradingDateTime.from_utc(utc_timestamp),
                        open=Money(row["Open"]),
                        high=Money(row["High"]),
                        low=Money(row["Low"]),
                        close=Money(row["Close"]),
                        volume=int(row["Volume"]),
                    )
                    bars.append(bar)
                except Exception as e:
                    accumulated_errors.append(e)
                    if len(accumulated_errors) / total_rows > 0.05:
                        span.add_event("bar_conversion_error_threshold_reached", {"errors": accumulated_errors})
                        span.set_status(trace.Status(trace.StatusCode.ERROR))
                        e = BarProviderException(f"Too many bar conversion failures")
                        span.record_exception(e)
                        raise e

            span.set_attribute("symbol_data_points_converted_to_bars", len(bars))
            span.set_attribute("symbol_data_points_conversion_errors", len(accumulated_errors))
            span.set_status(trace.Status(trace.StatusCode.OK))

            return bars

    def get_symbols(self) -> List[str]:
        return self._symbols

    async def get_current_bar(self, symbol: str) -> Money:
        with self._tracer.start_as_current_span("YFBarProvider.get_current_bar") as span:
            span.set_attribute("symbol", symbol)
            span.add_event("begin_current_bar_data_fetch")
            data = yf.download(symbol, period="1d", interval="15m", group_by="ticker")
            span.add_event("current_bar_data_fetch_complete")
            if yf.shared._ERRORS:
                error_msg = "; ".join(yf.shared._ERRORS.values())
                span.set_status(trace.Status(trace.StatusCode.ERROR))
                e = DataSourceException(f"YFinance errors: {error_msg}")
                span.record_exception(e)
                raise e

            if len(data) == 0:
                span.add_event("no_data_returned_for_symbol")
                span.set_status(trace.Status(trace.StatusCode.ERROR))
                e = DataSourceException(f"No data returned for symbol: {symbol}")
                span.record_exception(e)
                raise e

            try:
                symbol_data = data.xs(symbol, level=0, axis=1)
                bars = self._convert_df_to_bars(symbol_data)
                most_recent_bar = bars[-1]
                most_recent_bar.trading_datetime = TradingDateTime.now()
            except Exception as e:
                span.set_status(trace.Status(trace.StatusCode.ERROR))
                span.record_exception(e)
                raise
            else:
                span.set_status(trace.Status(trace.StatusCode.OK))
                return most_recent_bar

    async def get_bars(
        self,
        symbol: str,
        lookback: int,
    ) -> List[Bar]:
        with self._tracer.start_as_current_span("YFBarProvider.get_bars") as span:
            span.set_attribute("symbol", symbol)
            span.set_attribute("requested_lookback", lookback)
            if symbol not in self._data_cache:
                span.add_event("no_data_found_for_symbol")
                span.set_status(trace.Status(trace.StatusCode.ERROR))
                e = NoBarsForSymbolException(symbol)
                span.record_exception(e)
                raise e
            if len(self._data_cache[symbol]) < lookback:
                span.set_attribute("lookback_available_for_symbol", len(self._data_cache[symbol]))
                span.add_event("lookback_too_large_for_symbol")
                span.set_status(trace.Status(trace.StatusCode.ERROR))
                e = InsufficientBarsException(
                    f"Only {len(self._data_cache[symbol])} bars available for symbol: {symbol}"
                )
                span.record_exception(e)
                raise e
            try:
                bars = self._data_cache[symbol][-lookback:]
            except Exception as e:
                span.set_status(trace.Status(trace.StatusCode.ERROR))
                span.record_exception(e)
                raise
            else:
                span.set_status(trace.Status(trace.StatusCode.OK))
                return bars
