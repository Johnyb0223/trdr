from datetime import date, datetime, time, timezone
from dataclasses import dataclass

class TradingDateError(Exception):
    pass

@dataclass(frozen=True)
class TradingDateTime:
    """Value object representing a point in market time"""
    trading_date: date
    timestamp: datetime

    @classmethod
    def from_daily_close(cls, trading_date: date) -> 'TradingDateTime':
        """Create from just a trading date - timestamp is the last second of the day"""
        #should be a weekday
        if trading_date.weekday() not in [0, 1, 2, 3, 4]:
            raise TradingDateError("Trading date must be a weekday")
        return cls(trading_date, datetime.combine(trading_date, time(23, 59, 59, 999999)))

    @classmethod
    def from_utc(cls, timestamp: datetime) -> 'TradingDateTime':
        """Create from a UTC timestamp"""
        if timestamp.tzinfo != timezone.utc:
            raise TradingDateError("Timestamp must be UTC")
        #should be a weekday
        if timestamp.date().weekday() not in [0, 1, 2, 3, 4]:
            raise TradingDateError("Timestamp must be a weekday")
        return cls(timestamp.date(), timestamp)

    def is_same_session(self, other: 'TradingDateTime') -> bool:
        return self.trading_date == other.trading_date