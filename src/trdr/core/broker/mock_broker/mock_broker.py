from opentelemetry import trace
from decimal import Decimal
from typing import List

from ..base_broker import BaseBroker
from ..models import Order, Position, OrderStatus, OrderSide
from ...shared.models import Money
from ....test_utils.position_generator import PositionGenerator, PositionCriteria
from ...shared.models import TradingDateTime


class MockBroker(BaseBroker):

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        """Disabled constructor - use MockBroker.create() instead."""
        raise TypeError("Use MockBroker.create() instead to create a new broker")

    async def _initialize(self):
        with self._tracer.start_as_current_span("mock_broker._initialize") as span:
            self._pending_orders: List[Order] = []
            self._cash = Money(amount=Decimal(100000))
            positions = PositionGenerator(criteria=PositionCriteria(count=3)).generate_positions()
            self._positions: List[Position] = positions
            self._snapshot_of_positions: List[Position] = self._positions
            self._snapshot_of_cash = self._cash
            self._time_stamp = TradingDateTime.now()
            span.set_status(trace.StatusCode.OK)
            return

    async def _refresh_positions(self):
        with self._tracer.start_as_current_span("mock_broker._refresh_positions") as span:
            self._positions = self._snapshot_of_positions

            for order in self._pending_orders:
                order.status = OrderStatus.FILLED
                order.filled_at = TradingDateTime.now()
                for position in self._positions:
                    if order.symbol == position.symbol:
                        position.orders.append(order)
                        span.add_event(f"Added order to position {position.symbol}")
                        break
                else:
                    position = Position(symbol=order.symbol, orders=[order])
                    self._positions.append(position)
                    span.add_event(f"Created new position {position.symbol}")
                    self._snapshot_of_positions.append(position)

            self._pending_orders = []
            self._snapshot_of_positions = self._positions
            span.set_status(trace.StatusCode.OK)

    async def _refresh_cash(self):
        with self._tracer.start_as_current_span("mock_broker._refresh_cash") as span:
            self._cash = self._snapshot_of_cash
            new_orders = []
            for position in self._positions:
                new_orders.extend(position.get_orders_created_after_dt(self._time_stamp))

            for order in new_orders:
                if order.side == OrderSide.BUY:
                    if order.status in [OrderStatus.FILLED, OrderStatus.PARTIALLY_FILLED]:
                        self._cash -= order.amount
                else:
                    if order.status in [OrderStatus.FILLED, OrderStatus.PARTIALLY_FILLED]:
                        self._cash += order.amount

            self._snapshot_of_cash = self._cash
            self._time_stamp = TradingDateTime.now()

            span.set_status(trace.StatusCode.OK)

    async def _refresh_equity(self):
        with self._tracer.start_as_current_span("mock_broker._refresh_equity") as span:
            self._equity = self._cash + sum(position.get_market_value() for position in self._positions)
            span.set_status(trace.StatusCode.OK)

    async def _refresh_day_trade_count(self):
        self._day_trade_count = 1

    async def _place_order(self, order: Order) -> None:
        with self._tracer.start_as_current_span("mock_broker._place_order") as span:
            try:
                if not hasattr(self, "_pending_orders"):
                    self._pending_orders = []

                self._pending_orders.append(order)

                span.add_event(f"Added pending order: {order.side.value} {order.amount.amount} of {order.symbol}")
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.StatusCode.ERROR)
                raise
            else:
                span.set_status(trace.StatusCode.OK)

    async def _cancel_all_orders(self) -> None:
        with self._tracer.start_as_current_span("mock_broker._cancel_all_orders") as span:
            try:
                if hasattr(self, "_pending_orders"):
                    self._pending_orders = []
                    span.add_event("Cleared all pending orders")
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.StatusCode.ERROR)
                raise
            else:
                span.set_status(trace.StatusCode.OK)
