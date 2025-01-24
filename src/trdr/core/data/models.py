from decimal import Decimal
from stonks_shared.enums.timeframe import Timeframe
from trdr.core.time.trading_datetime import TradingDateTime
from trdr.core.money.money import Money


class BarValidationError(Exception):
    pass


class Bar:
    def __init__(
        self,
        trading_datetime: TradingDateTime,
        timeframe: Timeframe,
        open: Money,
        high: Money,
        low: Money,
        close: Money,
        volume: int,
    ):
        self._validate_prices(open, high, low, close)
        self._validate_volume(volume)

        self.trading_datetime = trading_datetime
        self.timeframe = timeframe
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume

    def _validate_prices(self, open: Money, high: Money, low: Money, close: Money) -> None:
        if not (low.amount <= high.amount):
            raise BarValidationError("Low price must be less than or equal to high price")
        if not (low.amount <= open.amount <= high.amount):
            raise BarValidationError("Open price must be between low and high prices")
        if not (low.amount <= close.amount <= high.amount):
            raise BarValidationError("Close price must be between low and high prices")

    def _validate_volume(self, volume: int) -> None:
        if volume < 0:
            raise BarValidationError("Volume cannot be negative")

    def __str__(self) -> str:
        return f"Bar(timestamp={self.trading_datetime}, timeframe={self.timeframe}, open={self.open}, high={self.high}, low={self.low}, close={self.close}, volume={self.volume})"
