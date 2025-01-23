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
        '''
        raises TradingDateError if the timestamp is not UTC or not a weekday
        '''
        if timestamp.tzinfo != timezone.utc:
            raise TradingDateError("Timestamp must be UTC")
        if timestamp.date().weekday() not in [0, 1, 2, 3, 4]:
            raise TradingDateError("Timestamp must be a weekday")
        return cls(timestamp.date(), timestamp.time())

    def __str__(self) -> str:
        return f"[{self.trading_date} {self.timestamp.strftime('%H:%M:%S')} UTC]"

    def __repr__(self) -> str:
        return self.__str__()
