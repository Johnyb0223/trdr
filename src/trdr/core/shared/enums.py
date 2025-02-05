from enum import Enum


class OrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(Enum):
    PENDING = "PENDING"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


class Timeframe(Enum):
    m1 = 60
    m2 = 120
    m5 = 300
    m15 = 900
    m30 = 1800
    m60 = 3600
    m90 = 5400
    h1 = 3600
    d1 = 86400
    d5 = 432000
    w1 = 604800
    mo1 = 2592000
    mo3 = 7776000

    @classmethod
    def is_intraday(cls, timeframe: "Timeframe") -> bool:
        return timeframe.value < 86400

    def __str__(self) -> str:
        name_map = {
            "m1": "1m",
            "m2": "2m",
            "m5": "5m",
            "m15": "15m",
            "m30": "30m",
            "m60": "60m",
            "m90": "90m",
            "h1": "1h",
            "d1": "1d",
            "d5": "5d",
            "w1": "1w",
            "mo1": "1mo",
            "mo3": "3mo",
        }
        str_representation = name_map.get(self.name, None)
        if not str_representation:
            raise ValueError(f"Could not convert {self.name} to string")
        return str_representation
