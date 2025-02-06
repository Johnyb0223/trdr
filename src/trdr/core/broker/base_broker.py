from abc import ABC, abstractmethod
import aiohttp
from typing import Optional, Type, TypeVar, Dict
from opentelemetry import trace
from opentelemetry.trace import NoOpTracer
from decimal import Decimal

from ..portfolio.models import Position, Security
from ..shared.models import Money
from .pdt.nun_strategy import NunStrategy
from .pdt.base_pdt_strategy import BasePDTStrategy

T = TypeVar("T", bound="BaseBroker")


class BaseBroker(ABC):
    """Base class for asynchronous broker implementations."""

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
        self._updated_dt = None
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
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.StatusCode.ERROR)
                raise
            else:
                span.set_status(trace.StatusCode.OK)

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
            if self._updated_dt is None:
                span.record_exception(
                    ValueError("Updated datetime is not initialized. The subclass _refresh() method must set this.")
                )
                span.set_status(trace.StatusCode.ERROR)
                raise ValueError("Updated datetime is not initialized. The _refresh() method must set this.")
            return self

    @abstractmethod
    def _initialize(self):
        pass

    @abstractmethod
    async def get_cash(self) -> Money:
        pass

    @abstractmethod
    async def get_position(self, security: Security) -> Optional[Position]:
        pass

    @abstractmethod
    async def get_positions(self) -> Optional[Dict[str, Position]]:
        pass

    @abstractmethod
    async def get_equity(self) -> Money:
        pass

    @abstractmethod
    async def get_account_exposure(self) -> Decimal:
        pass

    @abstractmethod
    async def get_position_exposure(self, security: Security) -> Decimal:
        pass

    async def __aenter__(self):
        """Enter the async context manager.

        Example:
            async with await Broker().create() as broker:
                cash = await broker.get_cash()

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
