from decimal import Decimal
from dataclasses import dataclass
from typing import Union
from datetime import date, datetime, time, timezone, timedelta

from trdr.core.shared.exceptions import TradingDateException


@dataclass(frozen=True)
class Money:
    """Value object representing monetary amounts in trading context.

    Attributes:
        amount (Decimal): The monetary amount
        currency (str): The currency code, defaults to USD

    Methods:
        __add__: Adds two Money objects of the same currency
    """

    amount: Decimal
    currency: str = "USD"  # Default to USD since most trading is in dollars

    def __init__(self, amount: Union[str, Decimal, Decimal], currency: str = "USD"):
        """Initialize a Money object.

        Args:
            amount: The monetary amount as string, Decimal or Decimal
            currency: The currency code, defaults to USD
        """
        # Use object.__setattr__ since we're frozen
        object.__setattr__(self, "amount", Decimal(str(amount)))
        object.__setattr__(self, "currency", currency)

    def __add__(self, other: "Money") -> "Money":
        """Add two Money objects.

        Args:
            other: Another Money object to add

        Returns:
            A new Money object with the sum

        Raises:
            ValueError: If currencies don't match
        """
        if self.currency != other.currency:
            raise ValueError(f"Cannot add different currencies: {self.currency} and {other.currency}")
        return Money(self.amount + other.amount, self.currency)

    def __str__(self) -> str:
        return f"{self.currency} {self.amount:.2f}"


@dataclass(frozen=True)
class TradingDateTime:
    """Value object representing a point in market time.

    Attributes:
        trading_date (date): The trading day date
        timestamp (datetime): The exact timestamp

    Methods:
        from_daily_close: Create from trading date, setting time to end of day
        from_utc: Create from UTC timestamp
        now: Create from current UTC time
    """

    trading_date: date
    timestamp: datetime

    @classmethod
    def from_daily_close(cls, trading_date: date) -> "TradingDateTime":
        """Create from just a trading date - timestamp is the last second of the day.

        Args:
            trading_date: The trading day date

        Returns:
            TradingDateTime set to end of provided date

        Raises:
            TradingDateException: If not a weekday
        """
        # should be a weekday
        if trading_date.weekday() not in [0, 1, 2, 3, 4]:
            raise TradingDateException("Trading date must be a weekday")
        return cls(trading_date, datetime.combine(trading_date, time(23, 59, 59, 999999)))

    @classmethod
    def from_utc(cls, timestamp: datetime) -> "TradingDateTime":
        """Create from a UTC timestamp.

        Args:
            timestamp: UTC datetime

        Returns:
            TradingDateTime for the timestamp

        Raises:
            TradingDateException: If timestamp not UTC or not weekday
        """
        if timestamp.tzinfo != timezone.utc:
            raise TradingDateException("Timestamp must be UTC")
        if timestamp.date().weekday() not in [0, 1, 2, 3, 4]:
            raise TradingDateException("Timestamp must be a weekday")
        return cls(timestamp.date(), timestamp)

    @classmethod
    def now(cls) -> "TradingDateTime":
        """Create from current UTC time.

        Returns:
            TradingDateTime for current time
        """
        return cls(datetime.now(tz=timezone.utc).date(), datetime.now(tz=timezone.utc))

    def __str__(self) -> str:
        return f"[{self.trading_date} {self.timestamp.strftime('%H:%M:%S')} UTC]"

    def __repr__(self) -> str:
        return self.__str__()

    def __add__(self, delta: timedelta) -> "TradingDateTime":
        """
        Add a timedelta to this TradingDateTime.

        Args:
            delta (timedelta): The time difference to add

        Returns:
            TradingDateTime: New instance with updated timestamp and trading_date

        Raises:
            TradingDateException: If the resulting trading date is not a weekday
        """
        if not isinstance(delta, timedelta):
            raise NotImplementedError("Cannot add non-timedelta to TradingDateTime")

        new_timestamp = self.timestamp + delta

        # Ensure the new date is a valid trading day (weekday)
        if new_timestamp.date().weekday() not in (0, 1, 2, 3, 4):
            raise TradingDateException("Resulting trading date is not a weekday")

        return TradingDateTime(new_timestamp.date(), new_timestamp)

    def __radd__(self, delta: timedelta) -> "TradingDateTime":
        return self.__add__(delta)
