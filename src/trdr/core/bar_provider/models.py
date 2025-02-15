from pydantic import BaseModel, model_validator

import random
from datetime import timedelta
from typing import List, Optional
from decimal import Decimal
from opentelemetry import trace
from pydantic import Field


from ..shared.models import TradingDateTime, Money, Timeframe
from .exceptions import BarValidationException


class Bar(BaseModel):
    trading_datetime: TradingDateTime
    open: Money
    high: Money
    low: Money
    close: Money
    volume: int

    @model_validator(mode="after")
    def check_values(self) -> "Bar":
        # Validate that the low price is less than or equal to high price.
        if self.low.amount > self.high.amount:
            raise BarValidationException("Low price must be less than or equal to high price")
        # Validate that open price is between low and high.
        if not (self.low.amount <= self.open.amount <= self.high.amount):
            raise BarValidationException("Open price must be between low and high prices")
        # Validate that close price is between low and high.
        if not (self.low.amount <= self.close.amount <= self.high.amount):
            raise BarValidationException("Close price must be between low and high prices")
        # Validate that the volume is non-negative.
        if self.volume < 0:
            raise BarValidationException("Volume cannot be negative")
        return self

    @classmethod
    def create_dummy_bars(cls, count: int, start_price: Money = Money(100)) -> List["Bar"]:
        bars = []
        current_price = start_price
        current_datetime = TradingDateTime.now()

        for _ in range(count):
            open_p = current_price.amount
            # A small random movement to simulate market changes
            price_change = Decimal(random.gauss(0, 1))  # mean=0, std=1
            close_p = open_p + price_change

            # Generate high and low values that surround open and close.
            high_p = max(open_p, close_p) + Decimal(random.gauss(0, 0.5))
            low_p = min(open_p, close_p) - Decimal(random.gauss(0, 0.5))

            # Simulate volume with random variation.
            volume = random.randint(800, 1200)

            bar = cls(
                trading_datetime=current_datetime,
                open=Money(open_p),
                high=Money(high_p),
                low=Money(low_p),
                close=Money(close_p),
                volume=volume,
            )

            bars.append(bar)

            # Prepare for the next iteration: use the current close as the next open.
            current_price = Money(close_p)
            # Increment the timestamp (here we add 1 minute between bars).
            current_datetime = current_datetime + timedelta(minutes=1)

        return bars

    def to_json(self) -> str:
        return self.model_dump_json(indent=2)

    def __str__(self) -> str:
        return (
            f"Bar(timestamp={self.trading_datetime}, open={self.open}, "
            f"high={self.high}, low={self.low}, close={self.close}, volume={self.volume})"
        )


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
        - Bars is a list with at least 200 entries
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
