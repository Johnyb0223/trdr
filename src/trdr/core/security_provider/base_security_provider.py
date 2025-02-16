from abc import ABC, abstractmethod
from typing import TypeVar, List, Optional, Type
from opentelemetry import trace

from ..bar_provider.base_bar_provider import BaseBarProvider
from .models import Security

T = TypeVar("T", bound="BaseSecurityProvider")


class BaseSecurityProvider(ABC):
    def __init__(
        self,
        bar_provider: BaseBarProvider,
        tracer: trace.Tracer,
    ):
        """Initialize the security provider.

        Args:
            bar_provider: Provider for fetching bar data
            tracer: OpenTelemetry tracer for monitoring
        """
        self._bar_provider = bar_provider
        self._tracer = tracer

    @classmethod
    async def create(
        cls: Type[T], bar_provider: BaseBarProvider, tracer: Optional[trace.Tracer] = trace.NoOpTracer()
    ) -> T:
        """Factory method to create a new security provider instance.

        Args:
            bar_provider: Provider for fetching bar data
            tracer: Optional OpenTelemetry tracer for monitoring

        Returns:
            A new instance of the security provider

        Raises:
            Any exceptions from _initialize()
        """
        self = cls.__new__(cls)
        BaseSecurityProvider.__init__(self, bar_provider, tracer)
        with self._tracer.start_as_current_span("BaseSecurityProvider.create") as span:
            try:
                await self._initialize()
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.StatusCode.ERROR)
                raise
            else:
                span.set_status(trace.StatusCode.OK)
        return self

    @abstractmethod
    async def _initialize(self) -> None:
        """Initialize the security provider.

        This method is called by create() and should contain any necessary setup logic.

        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError("This method must be implemented by user defined data providers")

    @abstractmethod
    async def get_security(self, symbol: str) -> Security:
        """Get security data for a specific symbol.

        Args:
            symbol: The ticker symbol to get security data for

        Returns:
            Security object containing the data for the requested symbol

        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError("This method must be implemented by user defined data providers")

    @abstractmethod
    async def get_security_list(self) -> List[Security]:
        """Get a list of all securities that this provider has data for.

        Returns:
            List of Security objects containing data for all available securities

        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError("This method must be implemented by user defined data providers")
