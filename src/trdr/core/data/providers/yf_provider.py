from typing import List, Optional
from datetime import datetime, timedelta, timezone
import yfinance as yf
import pandas as pd
import asyncio

from trdr.telemetry.instrumentation import TelemetryConfig, ExporterType, StatusCode, Status
from trdr.core.data.interfaces import DataProviderError
from trdr.core.data.base_data_provider import BaseDataProvider
from trdr.core.data.models import Bar
from trdr.core.time.trading_datetime import TradingDateTime
from stonks_shared.enums.timeframe import Timeframe
from trdr.core.money.money import Money


class YFProvider(BaseDataProvider):
    def __init__(
        self,
        symbols: List[str],
        timeframe: Timeframe = Timeframe.D1,
        telemetry_config: Optional[TelemetryConfig] = None,
    ):
        if len(symbols) > 600:
            raise DataProviderError("Yahoo Finance Provider does not support more than 600 symbols")
        super().__init__(symbols, timeframe, telemetry_config)

    async def _initialize(self) -> None:
        """
        This function is called by the factory method in the base class upon instantiation
        of a new provider.
        """
        with self._telemetry.span("YFProvider._initialize") as span:
            if span:
                span.set_attribute("symbols_count", len(self._symbols))
                span.set_attribute("symbols", ", ".join(self._symbols))
                span.set_attribute("timeframe", str(self._timeframe))

                with self._telemetry.span("YFProvider._initialize.fetch_data") as fetch_span:
                    if fetch_span:
                        fetch_span.set_attribute("symbols_count", len(self._symbols))
                    try:
                        data = await self._fetch_batch_stock_data(list(self._symbols))
                        if fetch_span:
                            fetch_span.set_attribute("data_shape", f"{data.shape[0]}x{data.shape[1]}")
                            fetch_span.add_event("data_fetched")
                    except Exception as e:
                        if fetch_span:
                            fetch_span.set_status(Status(StatusCode.FAILURE, str(e)))
                            fetch_span.record_exception(e)
                        raise DataProviderError(f"Error fetching data from Yahoo Finance: {e}") from e

                with self._telemetry.span("YFProvider._initialize.process_data") as process_span:
                    processed_symbols = 0

                    for symbol in self._symbols:
                        with self._telemetry.span("YFProvider._initialize.process_symbol") as symbol_span:
                            symbol_span.set_attribute("symbol", symbol) if symbol_span else None
                            try:
                                symbol_data = data.xs(symbol, level=0, axis=1)
                                if symbol_span:
                                    symbol_span.set_attribute("rows_retrieved_from_dataframe", len(symbol_data))
                                    symbol_span.add_event("symbol_data_retrieved_from_dataframe")
                                bars = self._convert_df_to_bars(symbol_data)
                                self._data_cache[symbol] = bars
                                if symbol_span:
                                    symbol_span.set_attribute("symbol_data_converted_to_bars", len(bars))
                                    symbol_span.add_event("symbol_data_converted_to_bars")
                                processed_symbols += 1
                            except Exception as e:
                                if symbol_span:
                                    symbol_span.set_status(Status(StatusCode.FAILURE, str(e)))
                                    symbol_span.record_exception(e)
                                raise DataProviderError(f"Error fetching data for symbol: {symbol}") from e

                    if process_span:
                        process_span.set_attribute("processed_symbols", processed_symbols)
                        process_span.add_event("processing_complete")

                if span:
                    span.set_status(Status(StatusCode.SUCCESS))
                    span.add_event("initialization_complete")

        self._initialized = True

    async def _fetch_batch_stock_data(
        self,
        tickers: List[str],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> pd.DataFrame:
        """
        raises DataProviderError on failure to fetch data from Yahoo Finance
        """
        with self._telemetry.span("YFProvider._fetch_batch_stock_data") as span:
            end_date = end_date or datetime.today().date()
            start_date = start_date or (end_date - timedelta(days=300))
            if span:
                span.set_attribute("tickers_count", len(tickers))
                span.set_attribute("tickers", ", ".join(tickers))
                span.set_attribute("start_date", str(start_date))
                span.set_attribute("end_date", str(end_date))
                span.set_attribute("date_range_days", (end_date - start_date).days)

            try:
                data = yf.download(tickers, start=start_date, end=end_date, group_by="ticker")
                if span:
                    span.set_attribute("rows_count", len(data))
                    span.set_attribute("empty_dataset", len(data) == 0)
                    span.add_event("download_complete")
                    span.set_status(Status(StatusCode.SUCCESS))
                return data
            except Exception as e:
                if span:
                    span.set_status(Status(StatusCode.FAILURE, str(e)))
                    span.record_exception(e)
                raise DataProviderError(f"Error fetching data from Yahoo Finance: {e}") from e

    def _convert_df_to_bars(self, df: pd.DataFrame) -> List[Bar]:
        with self._telemetry.span("YFProvider._convert_df_to_bars") as span:
            if span:
                span.set_attribute("rows_to_convert_bars", len(df))

            bars = []
            conversion_errors = 0

            for date, row in df.iterrows():
                try:
                    utc_timestamp = pd.Timestamp(date).to_pydatetime().replace(tzinfo=timezone.utc)
                    bar = Bar(
                        trading_datetime=TradingDateTime.from_utc(utc_timestamp),
                        timeframe=self._timeframe,
                        open=Money(row["Open"]),
                        high=Money(row["High"]),
                        low=Money(row["Low"]),
                        close=Money(row["Close"]),
                        volume=int(row["Volume"]),
                    )
                    bars.append(bar)
                except Exception as e:
                    conversion_errors += 1
                    if span:
                        span.add_event(
                            "bar_conversion_error",
                            {
                                "date": str(date),
                                "error": str(e),
                                "error_type": e.__class__.__name__,
                                "symbol": row["Symbol"],
                            },
                        )

            if span:
                span.set_attribute("converted_bars", len(bars))
                span.set_attribute("conversion_errors", conversion_errors)
                if conversion_errors > 0:
                    span.set_status(Status(StatusCode.FAILURE, f"Failed to convert {conversion_errors} bars"))
                else:
                    span.set_status(Status(StatusCode.SUCCESS))

            return bars

    async def get_bars(
        self,
        symbol: str,
        lookback: int,
    ) -> List[Bar]:
        """
        returns a list of bars of len(lookback) from oldest to newest
        raises DataProviderError if the provider is not initialized, if the symbol is not supported, or if there is not enough data to fetch the requested lookback
        """
        with self._telemetry.span("YFProvider.get_bars") as span:
            if span:
                span.set_attribute("symbol", symbol)
                span.set_attribute("lookback", lookback)

            try:
                if not self._initialized:
                    raise DataProviderError("DataProvider not initialized")

                if symbol not in self._data_cache:
                    if span:
                        span.set_attribute("available_symbols", list(self._data_cache.keys()))
                    raise DataProviderError(f"No data found for symbol: {symbol}")

                cached_bars_count = len(self._data_cache[symbol])
                if lookback > cached_bars_count:
                    raise DataProviderError(f"Not enough data to fetch {lookback} bars for symbol: {symbol}")

                if span:
                    span.set_attribute("available_bars", cached_bars_count)

                bars = []
                start_index = cached_bars_count - lookback
                for i in range(start_index, cached_bars_count):
                    bars.append(self._data_cache[symbol][i])

                if span:
                    span.set_attribute("returned_bars", len(bars))
                    span.set_status(Status(StatusCode.SUCCESS))

                return bars

            except DataProviderError as e:
                if span:
                    span.set_status(Status(StatusCode.FAILURE, str(e)))
                    span.record_exception(e)
                raise
            except Exception as e:
                if span:
                    span.set_status(Status(StatusCode.FAILURE, str(e)))
                    span.record_exception(e)
                raise DataProviderError(f"Unexpected error fetching bars: {e}") from e


if __name__ == "__main__":
    # telemetry config
    telemetry_config = TelemetryConfig(
        service_name="trdr",
        enable_traces=True,
        enable_metrics=True,
        exporter_type=ExporterType.CONSOLE,
        otlp_endpoint=None,
    )

    async def main():
        try:
            provider = await YFProvider.create(["AAPL", "MSFT", "GOOGL"], telemetry_config=telemetry_config)
            appl_bars = await provider.get_bars("AAPL", 20)
            for bar in appl_bars:
                print(bar)
        except Exception as e:
            print(e)

    asyncio.run(main())
