from typing import Optional, List
from datetime import timedelta
from .base_broker import BaseBroker
from ..portfolio.models import Position, Security, TradeContext, Order
from ..shared.models import Money, TradingDateTime
from ..portfolio.models import Side


class MockBroker(BaseBroker):
    """A mock broker implementation returning dummy data for testing purposes."""

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        """Disabled constructor - use T.create() instead."""
        raise TypeError("Use T.create() instead to create a new broker")

    async def _initialize(self):
        self._is_stale: bool = True
        await self._refresh()
        self.updated_dt: TradingDateTime = TradingDateTime.now()
        pass

    async def _refresh(self):
        self._is_stale = False
        self.updated_dt = TradingDateTime.now()
        return

    async def _is_stale(self) -> bool:
        if TradingDateTime.timestamp < TradingDateTime.timestamp - timedelta(min=10):
            self._is_stale = True
        return self._is_stale

    async def get_cash(self) -> Money:
        # Return a fixed cash amount.
        return Money(10000, "USD")

    async def get_position(self, security: Security) -> Optional[Position]:
        # Return a dummy position for the provided security.
        dummy_position = Position(quantity=10, average_price=Money(100, "USD"), side=Side.LONG)
        return dummy_position

    async def get_positions(self) -> Optional[List[Position]]:
        # Simulate a list with one dummy position.
        dummy_security = Security(symbol="DUMMY")
        dummy_position = Position(security=dummy_security, quantity=10, average_price=Money(100, "USD"))
        return [dummy_position]

    async def get_equity(self) -> Money:
        # Return a fixed equity value.
        return Money(15000, "USD")

    async def get_account_exposure(self) -> float:
        # Return a dummy account exposure (e.g., 50% exposure).
        return 0.5

    async def get_position_exposure(self, security: Security) -> float:
        # Return a dummy exposure for the given security.
        return 0.1

    async def place_order(self, trade_context: TradeContext, order: Order) -> None:
        self._is_stale = True
        return
