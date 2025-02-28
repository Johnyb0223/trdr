from opentelemetry import trace
from decimal import Decimal
from ..base_broker import BaseBroker
from ..models import Position, OrderSide, PositionSide
from ...shared.models import Money


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
            # Initialize tracking for positions opened today
            self._positions_opened_today = {}
            span.set_status(trace.StatusCode.OK)
            return

    async def _refresh(self) -> None:
        with self._tracer.start_as_current_span("mock_broker._refresh") as span:
            self._cash = Money(10000, "USD")
            
            # Create default positions
            position_aapl = Position(
                symbol="AAPL",
                quantity=Decimal(10),
                average_cost=Money(100, "USD"),
                side=PositionSide.LONG,
            )
            
            position_msft = Position(
                symbol="MSFT",
                quantity=Decimal(5),
                average_cost=Money(200, "USD"),
                side=PositionSide.LONG,
            )
            
            position_goog = Position(
                symbol="GOOG",
                quantity=Decimal(2),
                average_cost=Money(500, "USD"),
                side=PositionSide.LONG,
            )
            
            # Store positions
            self._positions = {
                position_aapl.symbol: position_aapl,
                position_msft.symbol: position_msft,
                position_goog.symbol: position_goog,
            }
            
            # Mark one position as opened today for testing
            if not hasattr(self, "_positions_opened_today"):
                self._positions_opened_today = {}
            self._positions_opened_today["MSFT"] = True
            
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

    async def _position_opened_today(self, symbol: str) -> bool:
        """
        Determine if a position was opened today.
        
        For the mock broker, this is configurable to simulate different scenarios.
        By default, positions are considered NOT opened today.
        
        Args:
            symbol: The ticker symbol to check
            
        Returns:
            bool: True if the position was opened today, False otherwise
        """
        with self._tracer.start_as_current_span("mock_broker._position_opened_today") as span:
            # For mock broker, we can track this with a set of positions opened today
            # Default implementation assumes no positions were opened today
            span.set_status(trace.StatusCode.OK)
            return getattr(self, "_positions_opened_today", {}).get(symbol, False)
            
    async def set_position_opened_today(self, symbol: str, opened_today: bool = True) -> None:
        """
        Mark a position as opened today for testing purposes.
        
        This method allows test code to simulate positions being opened today
        to test PDT rule enforcement.
        
        Args:
            symbol: The ticker symbol to mark
            opened_today: Whether to mark the position as opened today (True) or not (False)
        """
        with self._tracer.start_as_current_span("mock_broker.set_position_opened_today") as span:
            if not hasattr(self, "_positions_opened_today"):
                self._positions_opened_today = {}
                
            if opened_today:
                self._positions_opened_today[symbol] = True
            elif symbol in self._positions_opened_today:
                del self._positions_opened_today[symbol]
                
            span.set_status(trace.StatusCode.OK)
