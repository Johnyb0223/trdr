from enum import Enum
from dataclasses import dataclass
from decimal import Decimal
from trdr.core.time.trading_datetime import TradingDateTime
from trdr.core.money.money import Money
class OrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"

@dataclass
class OrderResult:
    """Value object representing order execution result"""
    order_id: str
    ticker: str
    side: OrderSide
    quantity: Decimal
    fill_price: Money
    fill_time: TradingDateTime
    status: str  # "FILLED", "PARTIAL", "REJECTED", etc.

@dataclass
class Position:
    """Value object representing a single position"""
    ticker: str
    quantity: Decimal
    entry_price: Money
    entry_date: TradingDateTime

    @property
    def market_value(self) -> Decimal:
        return self.quantity * self.entry_price