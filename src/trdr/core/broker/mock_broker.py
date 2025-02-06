from typing import Optional, Dict
from datetime import timedelta
from decimal import Decimal

from opentelemetry import trace

from .base_broker import BaseBroker
from ..portfolio.models import Position, Security, OrderSide, PositionSide
from ..shared.models import Money, TradingDateTime
from ..bar_provider.models import Bar


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
            try:
                await self._refresh()

                self.updated_dt: TradingDateTime = TradingDateTime.now()
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.StatusCode.ERROR)
                raise
            else:
                span.set_status(trace.StatusCode.OK)

    async def _refresh(self):
        with self._tracer.start_as_current_span("mock_broker._refresh") as span:
            try:
                self._cash = Money(10000, "USD")
                position = Position.create_dummy_position()
                self._positions = {position.symbol: position}
                self._equity = Money(15000, "USD")
                self._day_trade_count = 0
                self._updated_dt = TradingDateTime.now()
                self._is_stale_flag = False
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.StatusCode.ERROR)
                raise
            else:
                span.set_status(trace.StatusCode.OK)
                return

    def _is_stale(self) -> bool:
        if self.updated_dt.timestamp < TradingDateTime.now().timestamp - timedelta(minutes=10):
            self._is_stale_flag = True
        return self._is_stale_flag

    async def get_cash(self) -> Money:
        with self._tracer.start_as_current_span("mock_broker.get_cash") as span:
            try:
                if self._is_stale():
                    await self._refresh()
                cash = Money(10000, "USD")
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.StatusCode.ERROR)
                raise
            else:
                span.set_attribute("cash", str(cash))
                span.set_status(trace.StatusCode.OK)
                return cash

    async def get_position(self, security: Security) -> Optional[Position]:
        with self._tracer.start_as_current_span("mock_broker.get_position") as span:
            span.set_attribute("security", str(security))
            try:
                if self._is_stale():
                    await self._refresh()
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.StatusCode.ERROR)
                raise
            else:
                span.set_status(trace.StatusCode.OK)
                return self._positions.get(security.symbol, None)

    async def get_positions(self) -> Optional[Dict[str, Position]]:
        with self._tracer.start_as_current_span("mock_broker.get_positions") as span:
            try:
                if self._is_stale():
                    await self._refresh()
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.StatusCode.ERROR)
                raise
            else:
                span.set_attribute("positions_count", len(self._positions))
                span.set_status(trace.StatusCode.OK)
                return self._positions

    async def get_equity(self) -> Money:
        with self._tracer.start_as_current_span("mock_broker.get_equity") as span:
            try:
                if self._is_stale():
                    await self._refresh()
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.StatusCode.ERROR)
                raise
            else:
                span.set_attribute("equity", str(self._equity))
                span.set_status(trace.StatusCode.OK)
                return self._equity

    async def get_account_exposure(self) -> Decimal:
        with self._tracer.start_as_current_span("mock_broker.get_account_exposure") as span:
            try:
                if self._is_stale():
                    await self._refresh()
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.StatusCode.ERROR)
                raise
            else:
                if self._equity.amount == 0:
                    span.set_status(trace.StatusCode.OK)
                    span.set_attribute("account_exposure", "0")
                    return Decimal(0)
                exposure = (
                    sum([position.quantity * position.average_price.amount for position in self._positions.values()])
                    / self._equity.amount
                )
                span.set_attribute("account_exposure", str(exposure))
                span.set_status(trace.StatusCode.OK)
                return exposure

    async def get_position_exposure(self, security: Security) -> Optional[Decimal]:
        with self._tracer.start_as_current_span("mock_broker.get_position_exposure") as span:
            span.set_attribute("security", str(security))
            try:
                if self._is_stale():
                    await self._refresh()
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.StatusCode.ERROR)
                raise
            else:
                if self._equity.amount == 0:
                    span.set_status(trace.StatusCode.OK)
                    return None
                position = self._positions.get(security.symbol, None)
                if position is None:
                    span.set_status(trace.StatusCode.OK)
                    return Decimal(0)
                exposure = position.quantity * position.average_price.amount / self._equity.amount
                span.set_attribute("exposure", str(exposure))
                span.set_status(trace.StatusCode.OK)
                return exposure

    async def place_order(self, security: Security, side: OrderSide, dollar_amount: Money) -> None:
        with self._tracer.start_as_current_span("mock_broker.place_order") as span:
            span.set_attribute("security", str(security))
            span.set_attribute("side", str(side))
            span.set_attribute("dollar_amount", str(dollar_amount))
            try:
                if self._is_stale():
                    await self._refresh()
                # Simulate order placement in the mock broker.
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.StatusCode.ERROR)
                raise
            else:
                span.set_status(trace.StatusCode.OK)
                return
