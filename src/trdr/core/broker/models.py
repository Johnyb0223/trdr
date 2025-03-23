from enum import Enum
from decimal import Decimal
from typing import List
from pydantic import BaseModel, ConfigDict, model_validator

from ..shared.models import Money, TradingDateTime


class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    MARKET = "market"


class OrderStatus(Enum):
    PENDING = "PENDING"
    FILLED = "FILLED"
    PARTIAL_FILL = "PARTIAL_FILL"
    CANCELED = "CANCELED"
    REJECTED = "REJECTED"


class Order(BaseModel):
    symbol: str
    quantity_filled: Decimal | None = Decimal(0)
    side: OrderSide
    type: OrderType
    status: OrderStatus
    avg_fill_price: Money | None = None
    created_at: TradingDateTime
    filled_at: TradingDateTime | None = None
    time_in_force: str | None = "gtc"
    """
    The base_broker._validate_pre_order method needs to know the current price of the security to check if the trade would put us below the PDT minimum cash requirement (quantity_requested * current_price). If the trade does put us below the PDT minimum cash requirement, we need to enfore pdt rules as closing this position would result in a day trade since you fell below the PDT minimum cash requirement.
    """
    current_price: Money | None = None
    """
    At one point I had dollar_amount_requested as a property. This was so a user could specify either a dollar amount or a quantity. I removed it as quantity_requested is more flexible and captures the intent of the user. For example, the Alpaca API only supports dollar amounts if the order type is a market order and a time in force of "day". My hope was to reduce complexityvby only trading in number of shares.
    """
    quantity_requested: Decimal

    @property
    def net_quantity_filled(self) -> Decimal:
        return self.quantity_filled if self.side == OrderSide.BUY else -self.quantity_filled

    model_config = {"arbitrary_types_allowed": True}

    @model_validator(mode="after")
    def validate_order_state(self) -> "Order":
        """Validate that the order state is consistent."""
        status = self.status

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
            if self.current_price is None:
                raise ValueError("Pending orders must have a current_price")

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
        net_quantity = sum(order.net_quantity_filled for order in self.orders)
        return PositionSide.LONG if net_quantity > 0 else PositionSide.SHORT

    @property
    def get_market_value(self) -> Money:
        if len(self.orders) == 0:
            return Money(amount=Decimal(0))
        total_market_value = Decimal(0)
        for order in self.orders:
            if order.net_quantity_filled and order.avg_fill_price:
                total_market_value += abs(order.net_quantity_filled) * order.avg_fill_price.amount
        return Money(amount=total_market_value)

    @property
    def size(self) -> Decimal:
        if len(self.orders) == 0:
            return Decimal(0)
        return abs(sum(order.net_quantity_filled for order in self.orders))

    @property
    def average_cost(self) -> Money:
        if len(self.orders) == 0:
            return Money(amount=Decimal(0))
        if self.size == Decimal(0):
            return Money(amount=Decimal(0))
        return Money(
            amount=sum(order.net_quantity_filled * order.avg_fill_price.amount for order in self.orders) / self.size
        )

    def to_json(self) -> str:
        return self.model_dump_json()

    def __str__(self) -> str:
        return f"Position(symbol={self.symbol}, size={self.size}, average_cost={self.average_cost})"

    model_config = ConfigDict(arbitrary_types_allowed=True)
