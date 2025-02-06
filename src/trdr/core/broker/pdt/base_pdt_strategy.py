from typing import Optional, TypeVar, Type
from opentelemetry import trace
from abc import ABC, abstractmethod


T = TypeVar("T", bound="BasePDTStrategy")


class BasePDTStrategy(ABC):
    def __init__(self, tracer: Optional[trace.Tracer] = trace.NoOpTracer()):
        self._tracer = tracer

    @classmethod
    def create(cls: Type[T], tracer: Optional[trace.Tracer]) -> T:
        self = cls.__new__(cls)
        BasePDTStrategy.__init__(self, tracer=tracer)
        return self

    @abstractmethod
    def check_pdt_open_safely(self, number_of_positions_opened_today: int, rolling_day_trade_count: int) -> bool:
        raise NotImplementedError("check_pdt_open_safely must be implemented by subclasses")

    @abstractmethod
    def check_pdt_close_safely(self, position_opened_today: bool, rolling_day_trade_count: int) -> bool:
        raise NotImplementedError("check_pdt_close_safely must be implemented by subclasses")
