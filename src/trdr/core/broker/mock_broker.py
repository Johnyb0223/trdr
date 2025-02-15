from opentelemetry import trace

from .base_broker import BaseBroker
from .models import Position, OrderSide
from ..shared.models import Money


class MockBroker(BaseBroker):
    """A mock broker implementation returning dummy data for testing purposes."""

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        """Disabled constructor - use MockBroker.create() instead."""
        raise TypeError("Use MockBroker.create() instead to create a new broker")

    async def _initialize(self):
        with self._tracer.start_as_current_span("mock_broker._initialize") as span:
            span.set_status(trace.StatusCode.OK)
            return

    async def _refresh(self) -> None:
        with self._tracer.start_as_current_span("mock_broker._refresh") as span:
            self._cash = Money(10000, "USD")
            self._positions = {Position.create_dummy_position().symbol: Position.create_dummy_position()}
            self._equity = Money(15000, "USD")
            self._day_trade_count = 0
            span.set_status(trace.StatusCode.OK)

    async def _place_order(self, symbol: str, side: OrderSide, dollar_amount: Money) -> None:
        with self._tracer.start_as_current_span("mock_broker._execute_order") as span:
            try:
                pass
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.StatusCode.ERROR)
                raise
            else:
                span.set_status(trace.StatusCode.OK)

    async def _cancel_all_orders(self) -> None:
        with self._tracer.start_as_current_span("mock_broker._cancel_all_orders") as span:
            span.set_status(trace.StatusCode.OK)
            try:
                pass
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.StatusCode.ERROR)
                raise
            else:
                span.set_status(trace.StatusCode.OK)
