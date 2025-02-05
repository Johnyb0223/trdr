from abc import ABC, abstractmethod
from typing import List, Optional, Type, TypeVar

from opentelemetry import trace

from .models import Order, Security, TradeContext
from ..broker.base_broker import BaseBroker

T = TypeVar("T", bound="BasePortfolio")


class BasePortfolio:

    def __init__(self, broker: BaseBroker, tracer: Optional[trace.Tracer] = trace.NoOpTracer):
        self._telemetry = tracer
        self._broker = broker

    @classmethod
    async def create(cls: Type[T], broker: BaseBroker, tracer: Optional[trace.Tracer] = trace.NoOpTracer) -> T:
        self = cls.__new__(cls)
        BasePortfolio.__init__(self, broker, tracer)
        await self._initialize()
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
