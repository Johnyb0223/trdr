from abc import ABC, abstractmethod
from typing import List
from datetime import datetime
from stonks_shared.enums.timeframe import Timeframe
from trdr.core.data.bar import Bar


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