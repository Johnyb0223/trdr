from enum import Enum
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict

from ..shared.models import Money, TradingDateTime


class OrderStatus(Enum):
    """Represents the status of an order in the trading system.

    Values:
        PENDING: Order has been submitted but not yet executed
        FILLED: Order has been fully executed/filled
        CANCELLED: Order was cancelled before being filled
    """

    PENDING = "PENDING"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"

    def to_json(self) -> str:
        return self.value

    def __str__(self) -> str:
        return f"OrderStatus(value={self.value})"


class OrderSide(Enum):
    """Represents the side/direction of a trade or position.

    Values:
        BUY: Buy/long position
        SELL: Sell/short position
    """

    BUY = "BUY"
    SELL = "SELL"

    def to_json(self) -> str:
        return self.value


class Order(BaseModel):
    """Represents a trade order.

    Attributes:
        quantity: Number of shares/contracts to trade
        side: Whether to buy/long or sell/short
        status: Current status of the order
        timestamp: When the order was placed
    """

    quantity: Decimal
    side: OrderSide
    status: OrderStatus
    timestamp: TradingDateTime

    def to_json(self) -> str:
        return self.model_dump_json(indent=2)

    def __str__(self) -> str:
        return f"Order(quantity={self.quantity}, side={self.side}, status={self.status}, timestamp={self.timestamp})"

    model_config = ConfigDict(arbitrary_types_allowed=True)


class PositionSide(Enum):
    """Represents the side/direction of a trade or position.

    Values:
        LONG: Long/buy position
        SHORT: Short/sell position
    """

    LONG = "LONG"
    SHORT = "SHORT"

    def to_json(self) -> str:
        return self.value

    def __str__(self) -> str:
        return f"Side(value={self.value})"


class PositionStatus(Enum):
    """Represents the status of a position in the trading system.

    Values:
        OPEN: Position is open
        CLOSED: Position is closed
    """

    OPEN = "OPEN"
    CLOSED = "CLOSED"

    def to_json(self) -> str:
        return self.value


class Position(BaseModel):
    """Represents an open position in a security.

    Attributes:
        quantity: Number of shares/contracts held
        average_cost: Average price per share/contract
        side: Whether position is long or short
    """

    symbol: str
    quantity: Decimal
    average_cost: Money
    side: Optional[PositionSide]

    @classmethod
    def create_dummy_position(cls, symbol: str = "AAPL") -> "Position":
        return cls(
            symbol=symbol,
            quantity=10,
            average_cost=Money(100, "USD"),
            side=PositionSide.LONG,
        )

    def to_json(self) -> str:
        return self.model_dump_json(indent=2)

    def __str__(self) -> str:
        return f"Position(quantity={self.quantity}, average_cost={self.average_cost}, side={self.side})"

    model_config = ConfigDict(arbitrary_types_allowed=True)
