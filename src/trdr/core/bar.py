from datetime import datetime
from decimal import Decimal
from .timeframe import Timeframe

class Bar:
    def __init__(
        self,
        timestamp: datetime,
        timeframe: Timeframe,
        open: Decimal,
        high: Decimal,
        low: Decimal,
        close: Decimal,
        volume: int
    ):
        self.timestamp = timestamp
        self.timeframe = timeframe
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume