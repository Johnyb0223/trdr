from enum import Enum
from decimal import Decimal
from typing import List
from pydantic import BaseModel, ConfigDict, model_validator

from ..shared.models import Money, TradingDateTime


class OrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(Enum):
    MARKET = "MARKET"


class OrderStatus(Enum):
    PENDING = "PENDING"
    FILLED = "FILLED"
    PARTIAL_FILL = "PARTIAL_FILL"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class Order(BaseModel):
    symbol: str
    dollar_amount_requested: Money | None = None
    quantity_requested: Decimal | None = None
    quantity_filled: Decimal
    side: OrderSide
    type: OrderType
    status: OrderStatus
    avg_fill_price: Money | None = None
    created_at: TradingDateTime
    filled_at: TradingDateTime | None = None

    @property
    def net_quantity(self) -> Decimal:
        return self.quantity_filled if self.side == OrderSide.BUY else -self.quantity_filled

    model_config = {"arbitrary_types_allowed": True}

    @model_validator(mode="after")
    def validate_order_state(self) -> "Order":
        """Validate that the order state is consistent."""
        status = self.status

        if self.dollar_amount_requested is not None:
            if self.quantity_requested is not None:
                raise ValueError("Cannot specify both dollar_amount_requested and quantity_requested")
        if self.quantity_requested is not None:
            if self.dollar_amount_requested is not None:
                raise ValueError("Cannot specify both dollar_amount_requested and quantity_requested")

        if self.filled_at is not None and self.filled_at.is_weekend:
            raise ValueError("Orders can't be filled on a weekend")

        # Validation rules by status
        if status == OrderStatus.PENDING:
            if self.avg_fill_price is not None:
                raise ValueError("Pending orders cannot have a fill price")
            if self.quantity_filled != Decimal(0):
                raise ValueError("Pending orders must have quantity_filled = 0")
            if self.filled_at is not None:
                raise ValueError("Pending orders cannot have a filled_at time")

        elif status == OrderStatus.FILLED:
            if self.avg_fill_price is None:
                raise ValueError("Filled orders must have a fill price")
            if self.quantity_filled != self.quantity_requested:
                raise ValueError("Filled orders must have quantity_filled = quantity_requested")
            if self.filled_at is None:
                raise ValueError("Filled orders must have a filled_at timestamp")

        elif status == OrderStatus.PARTIAL_FILL:
            if self.avg_fill_price is None:
                raise ValueError("Partially filled orders must have a fill price")
            if self.quantity_filled >= self.quantity_requested:
                raise ValueError("Partially filled orders must have quantity_filled < quantity_requested")
            if self.quantity_filled <= Decimal(0):
                raise ValueError("Partially filled orders must have quantity_filled > 0")
            if self.filled_at is None:
                raise ValueError("Partially filled orders must have a filled_at timestamp")

        return self


class PositionSide(Enum):
    LONG = "LONG"
    SHORT = "SHORT"


class Position(BaseModel):

    symbol: str
    orders: List[Order]

    def get_orders_created_after_dt(self, dt: TradingDateTime) -> List[Order]:
        if len(self.orders) == 0:
            return []
        return [order for order in self.orders if order.created_at.timestamp >= dt.timestamp]

    @property
    def side(self) -> PositionSide:
        if len(self.orders) == 0:
            return None
        return PositionSide.LONG if self.size > 0 else PositionSide.SHORT

    @property
    def get_market_value(self) -> Money:
        if len(self.orders) == 0:
            return Money(amount=Decimal(0))
        total_market_value = Decimal(0)
        for order in self.orders:
            if order.net_quantity and order.avg_fill_price:
                total_market_value += abs(order.net_quantity) * order.avg_fill_price.amount
        return Money(amount=total_market_value)

    @property
    def size(self) -> Decimal:
        if len(self.orders) == 0:
            return Decimal(0)
        return sum(order.net_quantity for order in self.orders)

    @property
    def average_cost(self) -> Money:
        if len(self.orders) == 0:
            return Money(amount=Decimal(0))
        return Money(amount=sum(order.net_quantity * order.avg_fill_price.amount for order in self.orders) / self.size)

    def to_json(self) -> str:
        return self.model_dump_json()

    def __str__(self) -> str:
        return f"Position(symbol={self.symbol}, size={self.size}, average_cost={self.average_cost})"

    model_config = ConfigDict(arbitrary_types_allowed=True)
