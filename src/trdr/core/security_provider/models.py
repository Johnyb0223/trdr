from typing import List, Optional
from pydantic import BaseModel, model_validator, ConfigDict
from decimal import Decimal

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

    def compute_average_volume(self, period: Optional[Timeframe], offset: int = 0) -> int:
        """
        Compute the average volume over a given period.
        The offset allows looking back in time (offset=0 computes the current average, offset=1 for previous day's average, etc.).
        """
        if not period:
            raise ValueError("Period cannot be None")
        if period.is_intraday():
            raise ValueError("Intraday timeframe not supported for average volume computation")

        relevant_bars = self.bars.copy()
        days = period.to_days()

        if len(relevant_bars) < days + offset:
            return None

        # Calculate the start and end indices for the window
        end_idx = len(relevant_bars) - offset
        start_idx = end_idx - days

        # Sum the volumes for the specified window
        sum_volumes = sum(bar.volume for bar in relevant_bars[start_idx:end_idx])
        return sum_volumes // days

    def compute_moving_average(self, period: Optional[Timeframe], offset: int = 0) -> Money:
        """
        Compute the moving average over a given period.
        The offset allows looking back in time (offset=0 computes the current average, offset=1 for previous day's average, etc.).

        Args:
            period (Timeframe): Timeframe to average over.
            offset (int, optional): How many bars back to shift the window. Defaults to 0.

        Returns:
            Money: The computed moving average as a Money object.
        """
        if not period:
            raise ValueError("Period cannot be None")
        if period.is_intraday():
            raise ValueError("Intraday timeframe not supported for moving average computation")

        relevant_bars = self.bars.copy()
        days = period.to_days()

        if len(relevant_bars) < days + offset:
            return None

        # Calculate the start and end indices for the window
        end_idx = len(relevant_bars) - offset
        start_idx = end_idx - days

        # Sum the closing prices for the specified window
        sum_prices = sum(bar.close.amount for bar in relevant_bars[start_idx:end_idx])
        return Money(amount=Decimal(sum_prices / days))

    def has_bullish_moving_average_crossover(
        self, short_period: Optional[Timeframe], long_period: Optional[Timeframe]
    ) -> bool:
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
        if not short_period or not long_period:
            raise ValueError("Short or long period cannot be None")

        short_today = self.compute_moving_average(short_period)
        long_today = self.compute_moving_average(long_period)
        short_yesterday = self.compute_moving_average(short_period, 1)
        long_yesterday = self.compute_moving_average(long_period, 1)

        if None in (short_today, long_today, short_yesterday, long_yesterday):
            return None

        return short_yesterday.amount < long_yesterday.amount and short_today.amount > long_today.amount

    def has_bearish_moving_average_crossover(
        self, short_period: Optional[Timeframe], long_period: Optional[Timeframe]
    ) -> bool:
        """
        Determine if a bearish crossover occurred for two moving averages.
        That is, check if yesterday the short-term MA was above the long-term MA,
        and today the short-term MA has crossed below the long-term MA.

        Args:
            short_period (int): The period for the short-term moving average (e.g., 5 for MA5).
            long_period (int): The period for the long-term moving average (e.g., 20 for MA20).

        Returns:
            bool: True if a bearish crossover occurred, False otherwise.
        """
        if not short_period or not long_period:
            raise ValueError("Short or long period cannot be None")

        short_today = self.compute_moving_average(short_period)
        long_today = self.compute_moving_average(long_period)
        short_yesterday = self.compute_moving_average(short_period, 1)
        long_yesterday = self.compute_moving_average(long_period, 1)

        if None in (short_today, long_today, short_yesterday, long_yesterday):
            return None

        return short_yesterday.amount > long_yesterday.amount and short_today.amount < long_today.amount

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
        bars = values.bars
        current_bar = values.current_bar
        symbol = values.symbol

        if not isinstance(symbol, str):
            raise ValueError("Symbol must be a string")
        if not isinstance(bars, list):
            raise ValueError("Bars must be a list")
        if not isinstance(current_bar, Bar):
            raise ValueError("Current bar must be a Bar object")

        return values

    def to_json(self) -> str:
        return self.model_dump_json(indent=2)

    def __str__(self) -> str:
        """Returns a string representation of the Security.

        Returns:
            str: String containing symbol, current bar, moving averages and volumes
        """
        return f"Security(symbol={self.symbol}, current_bar={self.current_bar}, bars_count={len(self.bars)})"

    model_config = ConfigDict(arbitrary_types_allowed=True)
