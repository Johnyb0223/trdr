from abc import ABC, abstractmethod
from typing import List
from datetime import datetime
from .bar import Bar
from .timeframe import Timeframe

class DataProvider(ABC):
    @abstractmethod
    def get_bars(
        self, 
        symbol: str,
        timeframe: Timeframe,
        start: datetime,
        end: datetime
    ) -> List[Bar]:
        """Get historical bars for a symbol"""
        pass