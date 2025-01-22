from decimal import Decimal
from stonks_shared.enums.timeframe import Timeframe
from trdr.core.time.trading_datetime import TradingDateTime

class BarValidationError(Exception):
    pass

class Bar:
    def __init__(
        self,
        trading_datetime: TradingDateTime,
        timeframe: Timeframe,
        open: Decimal,
        high: Decimal,
        low: Decimal,
        close: Decimal,
        volume: int
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
    
    def _validate_prices(self, open: Decimal, high: Decimal, low: Decimal, close: Decimal) -> None:
        if not (low <= high):
            raise BarValidationError("Low price must be less than or equal to high price")
        if not (low <= open <= high):
            raise BarValidationError("Open price must be between low and high prices")
        if not (low <= close <= high):
            raise BarValidationError("Close price must be between low and high prices")
            
    def _validate_volume(self, volume: int) -> None:
        if volume < 0:
            raise BarValidationError("Volume cannot be negative")
