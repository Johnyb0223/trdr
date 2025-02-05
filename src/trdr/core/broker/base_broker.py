from abc import abstractmethod
import aiohttp
from typing import Optional, Type, TypeVar
from opentelemetry import trace
from opentelemetry.trace import NoOpTracer

from ..portfolio.models import Position, Security
from ..shared.models import Money

T = TypeVar("T", bound="BaseBroker")


class BaseBroker:
    """Base class for asynchronous broker implementations."""

    def __init__(
        self,
        telemetry: trace.Tracer = NoOpTracer(),
    ):
        """Initialize the broker with telemetry support.

        Args:
            telemetry: Telemetry manager instance for instrumentation
        """
        self._session = aiohttp.ClientSession()
        self._telemetry = telemetry

    @classmethod
    async def create(cls: Type[T], tracer: Optional[trace.Tracer] = trace.NoOpTracer) -> T:
        self = cls.__new__(cls)
        BaseBroker.__init__(self, tracer)
        await self._initialize()
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
    async def get_positions(self) -> Optional[list[Position]]:
        pass

    @abstractmethod
    async def get_equity(self) -> Money:
        pass

    @abstractmethod
    async def get_account_exposure(self) -> float:
        pass

    @abstractmethod
    async def get_position_exposure(self, security: Security) -> float:
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
