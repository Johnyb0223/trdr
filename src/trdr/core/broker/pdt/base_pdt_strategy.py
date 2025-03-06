from typing import Optional, TypeVar, Type
from opentelemetry import trace
from abc import ABC, abstractmethod

from .models import PDTContext, PDTDecision


T = TypeVar("T", bound="BasePDTStrategy")


class BasePDTStrategy(ABC):
    def __init__(self, tracer: Optional[trace.Tracer] = None):
        self._tracer = tracer if tracer is not None else trace.NoOpTracer()

    @classmethod
    def create(cls: Type[T], tracer: Optional[trace.Tracer] = None) -> T:
        self = cls.__new__(cls)
        BasePDTStrategy.__init__(self, tracer=tracer)
        return self

    @abstractmethod
    def evaluate_order(self, context: PDTContext) -> PDTDecision:
        """
        Evaluate a proposed order against PDT rules using the provided context.

        Args:
            context: A PDTContext object containing all relevant information

        Returns:
            A PDTDecision indicating whether the order is allowed and any modifications
        """
        raise NotImplementedError("evaluate_order must be implemented by subclasses")
