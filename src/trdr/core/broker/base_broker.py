from abc import ABC, abstractmethod
import aiohttp
from typing import Optional, Type, TypeVar, Dict
from opentelemetry import trace
from opentelemetry.trace import NoOpTracer
from decimal import Decimal
from datetime import timedelta

from .models import Position, OrderSide
from ..shared.models import Money, TradingDateTime
from .pdt.nun_strategy import NunStrategy
from .pdt.base_pdt_strategy import BasePDTStrategy

T = TypeVar("T", bound="BaseBroker")


class BaseBroker(ABC):

    def __init__(self, pdt_strategy: Optional[BasePDTStrategy], tracer: trace.Tracer):
        """Initialize the broker with tracer support.

        Args:
            tracer: tracer manager instance for instrumentation
        """
        self._session = aiohttp.ClientSession()
        self._pdt_strategy = pdt_strategy
        self._tracer = tracer
        self._positions = None
        self._cash = None
        self._equity = None
        self._day_trade_count = None
        self._updated_dt = TradingDateTime.now()
        self._is_stale_flag = True

    @classmethod
    async def create(
        cls: Type[T],
        pdt_strategy: Optional[BasePDTStrategy] = None,
        tracer: Optional[trace.Tracer] = NoOpTracer(),
    ) -> T:
        self = cls.__new__(cls)
        if not pdt_strategy:
            pdt_strategy = NunStrategy.create(tracer=tracer)
        BaseBroker.__init__(self, pdt_strategy=pdt_strategy, tracer=tracer)
        with self._tracer.start_as_current_span("BaseBroker.create") as span:
            try:
                await self._initialize()
                await self._stale_handler()
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.StatusCode.ERROR)
                raise
            else:
                span.set_status(trace.StatusCode.OK)

            return self

    @abstractmethod
    def _initialize(self):
        pass

    @abstractmethod
    async def _refresh(self):
        pass

    @abstractmethod
    async def _place_order(self, symbol: str, side: OrderSide, dollar_amount: Money) -> None:
        """
        Implement the low-level order placement logic specific to the subclass (e.g., interaction with the API).
        """
        pass

    @abstractmethod
    async def _cancel_all_orders(self) -> None:
        """
        Implement the low-level order cancellation logic specific to the subclass (e.g., interaction with the API).
        """
        pass

    async def get_available_cash(self) -> Money:
        with self._tracer.start_as_current_span("BaseBroker.get_cash") as span:
            await self._stale_handler()
            span.set_attribute("cash", str(self._cash))
            span.set_status(trace.StatusCode.OK)
            return self._cash

    async def get_position(self, symbol: str) -> Optional[Position]:
        with self._tracer.start_as_current_span("BaseBroker.get_position") as span:
            await self._stale_handler()
            position = self._positions.get(symbol, None)
            span.set_attribute("position", str(position))
            span.set_status(trace.StatusCode.OK)
            return position

    async def get_positions(self) -> Optional[Dict[str, Position]]:
        with self._tracer.start_as_current_span("BaseBroker.get_positions") as span:
            await self._stale_handler()
            span.set_attribute("positions_count", len(self._positions))
            span.set_status(trace.StatusCode.OK)
            return self._positions

    async def get_equity(self) -> Money:
        with self._tracer.start_as_current_span("BaseBroker.get_equity") as span:
            await self._stale_handler()
            span.set_attribute("equity", str(self._equity))
            span.set_status(trace.StatusCode.OK)
            return self._equity

    async def get_account_exposure(self) -> Decimal:
        with self._tracer.start_as_current_span("BaseBroker.get_account_exposure") as span:
            await self._stale_handler()
            if self._equity.amount == 0:
                span.set_status(trace.StatusCode.OK)
                span.set_attribute("account_exposure", "0")
                return Decimal(0)
            exposure = (
                sum([position.quantity * position.average_cost.amount for position in self._positions.values()])
                / self._equity.amount
            )
            span.set_attribute("account_exposure", str(exposure))
            span.set_status(trace.StatusCode.OK)
            return exposure

    async def get_position_exposure(self, symbol: str) -> Decimal:
        with self._tracer.start_as_current_span("BaseBroker.get_position_exposure") as span:
            await self._stale_handler()
            position = self._positions.get(symbol, None)
            if position is None:
                span.set_status(trace.StatusCode.OK)
                return Decimal(0)
            if self._equity.amount == 0:
                span.set_status(trace.StatusCode.OK)
                return Decimal(0)
            exposure = position.quantity * position.average_cost.amount / self._equity.amount
            span.set_attribute("exposure", str(exposure))
            span.set_status(trace.StatusCode.OK)
            return exposure

    async def place_order(self, symbol: str, side: OrderSide, dollar_amount: Money) -> None:
        """
        This is the concrete place_order method in BaseBroker.
        It performs a state refresh check, runs PDT logic, delegates to the implementation-specific _execute_order,
        and then marks the state as stale.
        """
        with self._tracer.start_as_current_span("BaseBroker.place_order") as span:
            await self._stale_handler()

            self._validate_pre_order(symbol, side)
            await self._place_order(symbol, side, dollar_amount)
            self._is_stale_flag = True
            span.set_status(trace.StatusCode.OK)
            span.add_event(
                "Order opened successfully: symbol={}, side={}, dollar_amount={}".format(symbol, side, dollar_amount)
            )

    async def cancel_all_orders(self) -> None:
        with self._tracer.start_as_current_span("BaseBroker.cancel_all_orders") as span:
            await self._cancel_all_orders()
            self._is_stale_flag = True
            await self._stale_handler()
            span.set_status(trace.StatusCode.OK)

    def _validate_pre_order(self, symbol: str, side: OrderSide) -> None:
        if side == OrderSide.BUY:
            allowed = self._pdt_strategy.check_pdt_open_safely(0, self._day_trade_count)
            if not allowed:
                raise Exception("PDT restrictions prevent opening a new position.")
        elif side == OrderSide.SELL:
            # In a full implementation the broker would determine if the existing position was opened today.
            position = self._positions.get(symbol)
            # Here we use a simplification: if the position exists, assume it was opened today.
            position_opened_today = bool(position)
            allowed = self._pdt_strategy.check_pdt_close_safely(position_opened_today, self._day_trade_count)
            if not allowed:
                raise Exception("PDT restrictions prevent closing this position.")
        # Additional common verifications can be incorporated here.

    def _clear_current_state(self) -> None:
        with self._tracer.start_as_current_span("BaseBroker._clear_current_state") as span:
            span.add_event("clearing current state")
            self._cash = None
            self._positions = None
            self._equity = None
            self._day_trade_count = None
            self._updated_dt = None
            span.set_status(trace.StatusCode.OK)

    def _is_state_in_good_order(self) -> None:
        with self._tracer.start_as_current_span("BaseBroker._is_state_in_good_order") as span:
            span.add_event("checking if state is in good order")
            if self._cash is None:
                span.record_exception(ValueError("Cash is not initialized"))
                span.set_status(trace.StatusCode.ERROR)
                raise ValueError("Cash is not initialized")
            if self._positions is None:
                span.record_exception(ValueError("Positions are not initialized"))
                span.set_status(trace.StatusCode.ERROR)
                raise ValueError("Positions are not initialized")
            if not isinstance(self._positions, dict):
                span.record_exception(
                    ValueError("BaseBroker.positions is not a dictionary of the form {symbol: Position}")
                )
                span.set_status(trace.StatusCode.ERROR)
                raise ValueError("BaseBroker.positions is not a dictionary of the form {symbol: Position}")
            for position in self._positions.values():
                if not isinstance(position, Position):
                    span.record_exception(ValueError("BaseBroker.positions contains non-Position objects"))
                    span.set_status(trace.StatusCode.ERROR)
                    raise ValueError("BaseBroker.positions contains non-Position objects")
            if self._equity is None:
                span.record_exception(
                    ValueError("Equity is not initialized. The subclass _refresh() method must set this.")
                )
                span.set_status(trace.StatusCode.ERROR)
                raise ValueError("Equity is not initialized. The subclass _refresh() method must set this.")
            if self._day_trade_count is None:
                span.record_exception(
                    ValueError("Day trade count is not initialized. The subclass _refresh() method must set this.")
                )
                span.set_status(trace.StatusCode.ERROR)
                raise ValueError("Day trade count is not initialized. The subclass _refresh() method must set this.")
            span.set_status(trace.StatusCode.OK)

    async def _stale_handler(self) -> bool:
        with self._tracer.start_as_current_span("BaseBroker._stale_handler") as span:
            # Use existing staleness logic (or refactor as needed)
            if self._updated_dt.timestamp < TradingDateTime.now().timestamp - timedelta(minutes=10):
                span.add_event("stale_state_detected due to timestamp difference")
                self._is_stale_flag = True
                span.add_event("_is_stale_flag set to True")

            if self._is_stale_flag:
                self._clear_current_state()
                await self._refresh()
                self._updated_dt = TradingDateTime.now()
                self._is_state_in_good_order()

            self._is_stale_flag = False
            span.add_event("_is_stale_flag set to False")
            span.set_status(trace.StatusCode.OK)

    async def __aenter__(self):
        """Enter the async context manager.

        Example:
            async with await Broker().create() as broker:
                cash = await broker.get_available_cash()

        Returns:
            self: The broker instance
        """
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the async context manager and cleanup resources.

        Args:
            exc_type: Exception type if an error occurred
            exc_val: Exception value if an error occurred
            exc_tb: Exception traceback if an error occurred
        """
        """Clean up resources by closing the aiohttp session."""
        if self._session:
            await self._session.close()
            self._session = None
