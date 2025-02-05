from typing import List
from datetime import timedelta, timezone
import yfinance as yf
import pandas as pd
import asyncio
from opentelemetry import trace

from ..exceptions import BarProviderException
from ..base_bar_provider import BaseBarProvider
from ..models import Bar, TradingDateTime, Money
from ...shared.enums import Timeframe


class YFBarProvider(BaseBarProvider):
    def __init__(
        self,
        *args,
        **kwargs,
    ):
        """Disabled constructor - use SecuritiesProvider.create() instead."""
        raise TypeError("Use T.create() instead to create a new securities provider")

    async def _initialize(self) -> None:
        """
        this function is called by the T.create() method implemented in the base class. Use that method to create a new securities provider.
        """
        if not self._symbols:
            raise BarProviderException("Symbols must be provided")
        if len(self._symbols) > 600:
            raise BarProviderException("Yahoo Finance Provider does not support more than 600 symbols")
        await self._refresh_data()

    async def _refresh_data(self) -> None:
        """
        This function is called by the factory method in the base class upon instantiation
        of a new provider.
        """
        with self._telemetry.start_as_current_span("YFSecuritiesProvider._refresh_data") as span:
            span.set_attribute("symbols_count", len(self._symbols))
            try:
                data = await self._fetch_batch_stock_data()
                span.set_attribute("data_shape", f"{data.shape[0]}x{data.shape[1]}")
                span.add_event("data_fetch_complete")
                span.set_status(trace.Status(trace.StatusCode.OK))
            except Exception as e:
                span.add_event("data_fetch_error")
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                raise BarProviderException(f"Error fetching data from Yahoo Finance: {e}")

            for symbol in self._symbols:
                try:
                    symbol_data = data.xs(symbol, level=0, axis=1)
                    bars = self._convert_df_to_bars(symbol_data)
                    self._data_cache[symbol] = bars
                except Exception as e:
                    span.add_event("symbol_data_conversion_error", {"symbol": symbol})
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    raise BarProviderException(f"Error converting data for symbol: {symbol} to bars")
            span.set_status(trace.Status(trace.StatusCode.OK))
            span.add_event("refresh_complete")

    async def _fetch_batch_stock_data(
        self,
    ) -> pd.DataFrame:

        with self._telemetry.start_as_current_span("YFSecuritiesProvider._fetch_batch_stock_data") as span:

            end_datetime = TradingDateTime.now().timestamp
            start_datetime = end_datetime - timedelta(days=300)

            span.set_attribute("total_symbols_to_fetch_data_for", len(self._symbols))
            span.set_attribute("start_datetime", str(start_datetime))
            span.set_attribute("end_datetime", str(end_datetime))
            span.set_attribute("date_range_days", (end_datetime - start_datetime).days)

            data = yf.download(
                self._symbols,
                start=start_datetime,
                end=end_datetime,
                group_by="ticker",
                interval=Timeframe.d1.__str__(),
            )

            if yf.shared._ERRORS:
                error_msg = "; ".join(yf.shared._ERRORS.values())
                span.add_event("download_error")
                span.set_status(trace.Status(trace.StatusCode.ERROR))
                span.record_exception(BarProviderException(f"YFinance errors: {error_msg}"))
                raise BarProviderException(f"YFinance errors: {error_msg}")

            span.set_attribute("empty_dataset", len(data) == 0)
            span.add_event("download_complete")
            span.set_status(trace.Status(trace.StatusCode.OK))
            return data

    def _convert_df_to_bars(self, df: pd.DataFrame) -> List[Bar]:
        with self._telemetry.start_as_current_span("YFProvider._convert_df_to_bars") as span:

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
                        raise BarProviderException(f"Too many bar conversion failures")

            if span:
                span.set_attribute("symbol_data_points_converted_to_bars", len(bars))
                span.set_attribute("symbol_data_points_conversion_errors", len(accumulated_errors))
                span.set_status(trace.Status(trace.StatusCode.OK))

            return bars

    async def get_current_bar(self, symbol: str) -> Money:
        with self._telemetry.start_as_current_span("YFProvider.get_current_price") as span:
            span.set_attribute("symbol", symbol)
            try:
                # Fetch the latest data from Yahoo Finance
                data = yf.download(symbol, period="1d", interval=Timeframe.m15.__str__(), group_by="ticker")
                if yf.shared._ERRORS:
                    error_msg = "; ".join(yf.shared._ERRORS.values())
                    span.add_event("download_error")
                    span.set_status(trace.Status(trace.StatusCode.ERROR))
                    span.record_exception(BarProviderException(f"YFinance errors: {error_msg}"))
                    raise BarProviderException(f"YFinance errors: {error_msg}")

                symbol_data = data.xs(symbol, level=0, axis=1)
                bars = self._convert_df_to_bars(symbol_data)
                most_recent_bar = bars[-1]
                most_recent_bar.trading_datetime = TradingDateTime.now()
                span.set_attribute("bar", str(most_recent_bar))
                span.set_status(trace.Status(trace.StatusCode.OK))
                return most_recent_bar
            except Exception as e:
                span.set_status(trace.Status(trace.StatusCode.ERROR))
                span.record_exception(e)
                raise

    async def get_bars(
        self,
        symbol: str,
        lookback: int,
    ) -> List[Bar]:
        with self._telemetry.start_as_current_span("YFProvider.get_bars") as span:
            span.set_attribute("symbol", symbol)
            span.set_attribute("lookback", lookback)
            if len(self._data_cache[symbol]) < lookback:
                span.set_attribute("lookback_available_for_symbol", len(self._data_cache[symbol]))
                span.add_event("lookback_too_large_for_symbol")
                span.set_status(trace.Status(trace.StatusCode.ERROR))
                raise BarProviderException(f"Only {len(self._data_cache[symbol])} bars available for symbol: {symbol}")
            if symbol not in self._data_cache:
                span.add_event("no_data_found_for_symbol")
                span.set_status(trace.Status(trace.StatusCode.ERROR))
                raise BarProviderException(f"No data found for symbol: {symbol}")
            try:
                cached_bars_count = len(self._data_cache[symbol])
                span.set_attribute("available_bars", cached_bars_count)
                bars = self._data_cache[symbol][-lookback:]
                span.set_attribute("returned_bars", len(bars))
                span.set_status(trace.Status(trace.StatusCode.OK))
                return bars
            except Exception as e:
                span.set_status(trace.Status(trace.StatusCode.ERROR))
                span.record_exception(e)
                raise


if __name__ == "__main__":
    """
    this is an example of how a securities provider can be created and used within a script. This also shouws how to set up a global tracer provider and how to use it to create a tracer for a specific component.
    """

    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

    async def main():
        provider = TracerProvider()
        span_processor = BatchSpanProcessor(ConsoleSpanExporter())
        provider.add_span_processor(span_processor)
        trace.set_tracer_provider(provider)
        tracer = trace.get_tracer("trdr")
        try:
            provider = await YFBarProvider.create(["AAPL", "MSFT", "GOOGL"], tracer)
            current_bar = await provider.get_current_bar("AAPL")
            for symbol in provider._symbols:
                current_bar = await provider.get_current_bar(symbol)
                print(current_bar)
                bars = await provider.get_bars(symbol, 20)
                for bar in bars:
                    print(bar)
        except Exception as e:
            print(e)

    asyncio.run(main())
