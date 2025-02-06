from abc import ABC, abstractmethod
from typing import Protocol, List
from trdr.core.shared.enums import Timeframe
from trdr.core.shared.models import Bar


class ILogicalExpression(Protocol):
    """Interface for all logical expressions (conditions and groups)"""

    def evaluate(self) -> bool:
        """Evaluate the logical expression"""
        pass


class ICondition(Protocol):
    """Interface for conditions like 'MA20 > MA50'"""

    def evaluate(self) -> bool:
        """Evaluate the condition"""
        pass


class IIndicator(ABC):
    def __init__(self, bars: List[Bar], timeframe: Timeframe):
        self.bars = bars
        self.timeframe = timeframe

    @abstractmethod
    def value(self) -> Decimal:
        """Calculate and return the indicator's current value"""
        pass
