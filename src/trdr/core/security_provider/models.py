from typing import List, Optional
from opentelemetry import trace
from pydantic import BaseModel, model_validator, Field

from ..bar_provider.models import Bar
from ..shared.models import Money, Timeframe


class Security(BaseModel):
    """A class representing a tradable security with price and volume data.

    Attributes:
        symbol (str): The ticker symbol for the security
        current_bar (Bar): The most recent price/volume bar
        bars (List[Bar]): Historical price/volume bars (minimum 200 required)
        tracer (Optional[trace.Tracer]): Opentracer tracer for monitoring

    Methods:
        validate_fields: Validates the security attributes
        get_current_price: Returns the current price
        get_X_day_moving_average: Returns X-day moving average price (X=5,20,50,100,200)
        get_X_day_average_volume: Returns X-day average volume (X=5,20,50,100,200)
    """

    symbol: str
    current_bar: Bar
    bars: List[Bar]
    tracer: Optional[trace.Tracer] = Field(default=trace.NoOpTracer(), exclude=True)

    def get_current_price(self) -> Money:
        """Returns the current price of the security.

        Returns:
            Money: The current price
        """
        return self.current_bar.close

    def get_current_volume(self) -> int:
        """Returns the current volume of the security.

        Returns:
            int: The current volume
        """
        return self.current_bar.volume

    def compute_average_volume(self, period: Timeframe, offset: int = 0) -> Optional[Money]:
        """
        Compute the average volume over a given period.
        The offset allows looking back in time (offset=0 computes the current average, offset=1 for previous day's average, etc.).
        """
        relevant_bars = self.bars.copy()
        if offset:
            # Remove the most recent 'offset' bars to simulate calculation from a previous day.
            relevant_bars = relevant_bars[:-offset]
        if len(relevant_bars) < period.to_days():
            return None
        index = period.to_days()
        sum_volumes = sum(bar.volume for bar in relevant_bars[-index:])
        return Money(sum_volumes // index)

    def compute_moving_average(self, period: Timeframe, offset: int = 0) -> Optional[Money]:
        """
        Compute the moving average over a given period.
        The offset allows looking back in time (offset=0 computes the current average, offset=1 for previous day's average, etc.).

        Args:
            period (int): Number of bars to average over.
            offset (int, optional): How many bars back to shift the window. Defaults to 0.

        Returns:
            Optional[Money]: The computed moving average as a Money object, or None if insufficient data.
        """
        # Make a copy so we don't modify the actual list.
        relevant_bars = self.bars.copy()
        if offset:
            # Remove the most recent 'offset' bars to simulate calculation from a previous day.
            relevant_bars = relevant_bars[:-offset]
        if len(relevant_bars) < period.to_days():
            return None
        index = period.to_days()
        sum_prices = sum(bar.close.amount for bar in relevant_bars[-index:])
        return Money(sum_prices / index)

    def has_bullish_moving_average_crossover(self, short_period: Timeframe, long_period: Timeframe) -> bool:
        """
        Determine if a bullish crossover occurred for two moving averages.
        That is, check if yesterday the short-term MA was below the long-term MA,
        and today the short-term MA has crossed above the long-term MA.

        Args:
            short_period (int): The period for the short-term moving average (e.g., 5 for MA5).
            long_period (int): The period for the long-term moving average (e.g., 20 for MA20).

        Returns:
            bool: True if a bullish crossover occurred, False otherwise.
        """
        short_today = self.compute_moving_average(short_period, offset=0)
        long_today = self.compute_moving_average(long_period, offset=0)
        short_yesterday = self.compute_moving_average(short_period, offset=1)
        long_yesterday = self.compute_moving_average(long_period, offset=1)

        if None in (short_today, long_today, short_yesterday, long_yesterday):
            return False

        return short_yesterday.amount < long_yesterday.amount and short_today.amount > long_today.amount

    @model_validator(mode="after")
    def validate_fields(cls, values):
        """Validates the security fields.

        Checks:
        - Symbol is a string
        - Current bar is a valid Bar object

        Args:
            values: The model instance being validated

        Returns:
            The validated model instance

        Raises:
            ValueError: If any validation checks fail
        """
        tracer = values.tracer
        bars = values.bars
        current_bar = values.current_bar
        symbol = values.symbol

        with tracer.start_as_current_span("Security.validate_fields") as span:
            # Validate symbol
            if not isinstance(symbol, str):
                span.set_status(trace.StatusCode.ERROR)
                span.record_exception(ValueError("Symbol must be a string"))
                raise ValueError("Symbol must be a string")
            span.set_attribute("symbol", symbol)
            span.add_event("symbol_validated")
            # Validate bars
            if not isinstance(bars, list):
                span.set_status(trace.StatusCode.ERROR)
                span.record_exception(ValueError("Bars must be a list"))
                raise ValueError("Bars must be a list")
            span.add_event("bars_validated")

            # Validate current_bar
            if not isinstance(current_bar, Bar):
                span.set_status(trace.StatusCode.ERROR)
                span.record_exception(ValueError("Current bar must be a Bar object"))
                raise ValueError("Current bar must be a Bar object")
            span.add_event("current_bar_validated")

            span.set_status(trace.StatusCode.OK)
            span.add_event("security_validated")

        return values

    @classmethod
    def create_dummy_security(cls, symbol: str = "AAPL") -> "Security":
        bars = Bar.create_dummy_bars(count=200)
        return cls(
            symbol=symbol,
            current_bar=bars[-2],
            bars=bars,
        )

    def to_json(self) -> str:
        return self.model_dump_json(exclude={"tracer"}, indent=2)

    def __str__(self) -> str:
        """Returns a string representation of the Security.

        Returns:
            str: String containing symbol, current bar, moving averages and volumes
        """
        return f"Security(symbol={self.symbol}, current_bar={self.current_bar}, bars_count={len(self.bars)})"

    class Config:
        arbitrary_types_allowed = True
