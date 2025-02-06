from abc import ABC, abstractmethod
from typing import List, Optional, Type, TypeVar

from opentelemetry import trace

from .models import Order, Security, TradeContext
from ..broker.base_broker import BaseBroker

T = TypeVar("T", bound="BasePortfolio")


class BasePortfolio:

    def __init__(self, broker: BaseBroker, tracer: Optional[trace.Tracer] = trace.NoOpTracer):
        self._tracer = tracer
        self._broker = broker

    @classmethod
    async def create(cls: Type[T], broker: BaseBroker, tracer: Optional[trace.Tracer] = trace.NoOpTracer) -> T:
        self = cls.__new__(cls)
        BasePortfolio.__init__(self, broker, tracer)
        with self._tracer.start_as_current_span("BasePortfolio.create") as span:
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
    async def get_trade_context(self, security: Security) -> TradeContext:
        raise NotImplementedError("This method must be implemented by user defined data providers")

    @abstractmethod
    async def place_order(self, trade_context: TradeContext, order: Order) -> None:
        raise NotImplementedError("This method must be implemented by user defined data providers")
