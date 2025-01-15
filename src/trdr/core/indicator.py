from abc import ABC, abstractmethod
from .timeframe import Timeframe
from .data_provider import DataProvider

class Indicator(ABC):
    def __init__(self, data_provider: DataProvider, timeframe: Timeframe):
        self.data_provider = data_provider
        self.timeframe = timeframe
    
    @abstractmethod
    def value(self) -> float:
        """Calculate and return the indicator's current value"""
        pass