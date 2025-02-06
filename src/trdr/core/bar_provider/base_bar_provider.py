from typing import List, Type, Optional, TypeVar
from abc import ABC, abstractmethod
from opentelemetry import trace

from .models import Bar

T = TypeVar("T", bound="BaseBarProvider")


class BaseBarProvider(ABC):
    def __init__(
        self,
        symbols: List[str],
        tracer: trace.Tracer,
    ):
        self._symbols = set(symbols)
        self._data_cache = {}
        self._tracer = tracer

    @classmethod
    async def create(cls: Type[T], symbols: List[str], tracer: Optional[trace.Tracer] = trace.NoOpTracer) -> T:
        self = cls.__new__(cls)
        BaseBarProvider.__init__(self, symbols, tracer)
        with self._tracer.start_as_current_span("BaseBarProvider.create") as span:
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
        raise NotImplementedError("This method must be implemented by user defined data providers")

    @abstractmethod
    def get_current_bar(self, symbol: str) -> Bar:
        raise NotImplementedError("This method must be implemented by user defined data providers")

    @abstractmethod
    def get_bars(self, symbol: str, lookback: int) -> List[Bar]:
        raise NotImplementedError("This method must be implemented by user defined data providers")
