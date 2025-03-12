from typing import List, Set
from decimal import Decimal
import random
import datetime
from pydantic import BaseModel, ConfigDict

from ..core.broker.models import Position, Order, OrderSide, OrderStatus
from ..core.shared.models import Money, TradingDateTime
from .order_generator import OrderGenerator, OrderCriteria


class PositionCriteria(BaseModel):
    """Criteria for generating positions"""

    symbols: List[str] = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "SMR", "GME"]
    count: int = 5
    orders_per_position: tuple[int, int] = (3, 10)  # Min and max orders per position
    net_position_bias: float = 0.5  # Probability of net long position (vs. short)
    min_order_value: Money = Money(amount=Decimal("500"))
    max_order_value: Money = Money(amount=Decimal("5000"))
    allow_duplicates: bool = False  # Whether to allow the same symbol to appear in multiple positions

    model_config = ConfigDict(arbitrary_types_allowed=True)


class PositionGenerator:
    """Generates realistic trading positions with order history"""

    def __init__(self, criteria: PositionCriteria):
        self.criteria = criteria

    def generate_positions(self) -> List[Position]:
        """Generate positions based on criteria"""
        positions = []
        available_symbols = self.criteria.symbols.copy()

        # Check if we have enough unique symbols
        if not self.criteria.allow_duplicates and len(available_symbols) < self.criteria.count:
            raise ValueError(
                f"Not enough unique symbols ({len(available_symbols)}) "
                f"to generate {self.criteria.count} positions without duplicates. "
                f"Set allow_duplicates=True or provide more symbols."
            )

        for _ in range(self.criteria.count):
            # Pick a unique symbol if duplicates aren't allowed
            if not self.criteria.allow_duplicates:
                if not available_symbols:
                    break  # No more symbols available

                symbol = random.choice(available_symbols)
                available_symbols.remove(symbol)
            else:
                # Allow duplicates - just pick any symbol
                symbol = random.choice(self.criteria.symbols)

            # Determine how many orders to generate for this position
            min_orders, max_orders = self.criteria.orders_per_position
            num_orders = random.randint(min_orders, max_orders)

            # Determine if we want a net long or short position
            is_net_long = random.random() < self.criteria.net_position_bias

            if is_net_long:
                order_criteria = OrderCriteria(
                    count=num_orders,
                    symbol=symbol,
                    side=OrderSide.BUY,
                    status=OrderStatus.FILLED,  # Default to FILLED orders for positions
                    price_range=(Decimal("50"), Decimal("200")),
                )
            else:
                order_criteria = OrderCriteria(
                    count=num_orders,
                    symbol=symbol,
                    side=OrderSide.SELL,
                    status=OrderStatus.FILLED,  # Default to FILLED orders for positions
                    price_range=(Decimal("50"), Decimal("200")),
                )

            # Generate orders
            order_gen = OrderGenerator(order_criteria)
            orders = order_gen.generate_orders()

            # Ensure net position matches desired direction
            self._adjust_orders_for_net_position(orders, is_net_long)

            # Create position
            position = Position(symbol=symbol, orders=orders)

            positions.append(position)

        return positions

    def _adjust_orders_for_net_position(self, orders: List[Order], is_net_long: bool) -> None:
        """Adjust orders to ensure the position is net long or short as requested"""
        # Calculate initial net position using quantity_filled for orders
        net_quantity = sum(
            order.quantity_filled if order.side == OrderSide.BUY else -order.quantity_filled
            for order in orders
            if order.status in [OrderStatus.FILLED, OrderStatus.PARTIAL_FILL]
        )

        # Determine if we need to adjust
        needs_adjustment = (is_net_long and net_quantity <= 0) or (not is_net_long and net_quantity >= 0)

        if needs_adjustment:
            # Calculate how much we need to adjust by
            adjustment_qty = abs(net_quantity) + Decimal(random.randint(1, 10))

            # Find a random order to modify
            order_idx = random.randint(0, len(orders) - 1)
            order = orders[order_idx]

            # Adjust the order - ensure it's FILLED for consistency
            if is_net_long:
                order.side = OrderSide.BUY
                order.status = OrderStatus.FILLED
                order.quantity_requested = adjustment_qty
                order.quantity_filled = adjustment_qty  # For FILLED orders, filled must equal requested
            else:
                order.side = OrderSide.SELL
                order.status = OrderStatus.FILLED
                order.quantity_requested = adjustment_qty
                order.quantity_filled = adjustment_qty  # For FILLED orders, filled must equal requested

            # Ensure the avg_fill_price is set for FILLED orders
            if order.avg_fill_price is None:
                order.avg_fill_price = Money(amount=Decimal("100.00"))

            # Ensure filled_at is set for FILLED orders
            if order.filled_at is None:
                fill_time = order.created_at.timestamp + datetime.timedelta(minutes=random.randint(1, 60))
                order.filled_at = TradingDateTime.from_utc(fill_time)


if __name__ == "__main__":
    criteria = PositionCriteria(
        count=5,
        orders_per_position=(2, 5),
        net_position_bias=0.7,  # 70% chance of net long positions
    )
    generator = PositionGenerator(criteria)
    positions = generator.generate_positions()

    for position in positions:
        # Calculate net quantity based on filled quantities
        net_qty = sum(
            order.quantity_filled if order.side == OrderSide.BUY else -order.quantity_filled
            for order in position.orders
        )
        print(f"{position.symbol}: {len(position.orders)} orders, net quantity: {net_qty}")
