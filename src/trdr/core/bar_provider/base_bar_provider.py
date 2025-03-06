from typing import List, Type, Optional, TypeVar
from abc import ABC, abstractmethod
from opentelemetry import trace

from .models import Bar

T = TypeVar("T", bound="BaseBarProvider")


class BaseBarProvider(ABC):
    """
    Abstract base class for retrieving and managing OHLCV bar data for securities.

    This class defines the interface that all bar providers must implement, setting
    a standardized way to retrieve historical and current price data. Bar providers
    serve as the data foundation for trading strategies.

    All implementations should maintain a data cache for efficient data retrieval
    and support OpenTelemetry instrumentation for monitoring and tracing.

    Attributes:
        _data_cache: Internal cache for storing retrieved bar data
        _tracer: OpenTelemetry tracer for instrumenting operations
    """

    def __init__(
        self,
        tracer: trace.Tracer,
    ):
        self._data_cache = {}
        self._tracer = tracer

    @classmethod
    async def create(cls: Type[T], symbols: List[str], tracer: Optional[trace.Tracer] = trace.NoOpTracer()) -> T:
        """
        Factory method to create and initialize a bar provider instance.

        This async factory method pattern ensures proper initialization of resources
        and error handling during the creation process. It invokes the implementation-specific
        _initialize method which must be defined by concrete subclasses.

        Args:
            symbols: List of ticker symbols to initialize the provider with
            tracer: OpenTelemetry tracer for instrumenting operations

        Returns:
            An initialized instance of the concrete bar provider

        Raises:
            Various exceptions depending on the implementation, typically related to
            data availability or connectivity issues
        """
        self = cls.__new__(cls)
        BaseBarProvider.__init__(self, tracer)
        with self._tracer.start_as_current_span("BaseBarProvider.create") as span:
            try:
                await self._initialize(symbols)
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.StatusCode.ERROR)
                raise
            else:
                span.set_status(trace.StatusCode.OK)
        return self

    @abstractmethod
    async def _initialize(self, symbols: List[str]) -> None:
        """
        This abstract method MUST be implemented by user defined data providers.
        - This method SHOULD use the symbols argument to initialize the data cache.
        - After the method has completed, the self._data_cache dictionary MUST be a dictionary where the keys are the symbols and the values are lists of Bars.
        - The self._data_cache dictionary must only contain key,value pairs for symbols that have data available.
        """
        raise NotImplementedError("This method must be implemented by user defined data providers")

    @abstractmethod
    async def get_symbols(self) -> List[str]:
        """
        Get the list of symbols with data available.

        Returns:
            List[str]: List of symbols.
        """
        pass

    @abstractmethod
    async def get_bars(self, symbol: str, lookback: Optional[int] = None) -> List[Bar]:
        """Get bars for a specific symbol.

        Args:
            symbol: The ticker symbol to get bars for
            lookback: The number of bars to return

        Raises:
            NoBarsForSymbolException: If the symbol is not found in the data cache
            InsufficientBarsException: If the number of bars requested is greater than the number of bars available
        """
        raise NotImplementedError("This method must be implemented by user defined data providers")

    @abstractmethod
    async def get_current_bar(self, symbol: str) -> Bar:
        """
        Get the current bar for a symbol.

        Args:
            symbol (str): The symbol to get the current bar for.

        Returns:
            Bar: The current bar for the symbol.

        Raises:
            BarProviderException: If we receive an error not associated with the symbol of interest or if we receive an error not related to a no data error.
            NoBarsForSymbolException: If we didn't receive any data for the symbol of interest.
        """
        pass
