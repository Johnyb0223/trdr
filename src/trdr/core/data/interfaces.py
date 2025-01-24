from abc import ABC, abstractmethod
from typing import List, Set
from trdr.core.data.models import Bar
from trdr.core.time.trading_datetime import TradingDateTime
from stonks_shared.enums.timeframe import Timeframe


class DataProviderError(Exception):
    pass


class SymbolNotSupportedError(DataProviderError):
    pass


class TimeframeNotSupportedError(DataProviderError):
    pass


class IDataProvider(ABC):
    """Interface for data providers"""

    @abstractmethod
    async def create(cls, symbols: List[str], timeframe: Timeframe = Timeframe.D1) -> "IDataProvider":
        """Factory method for creating and initializing provider"""
        pass

    @abstractmethod
    async def _initialize(self) -> None:
        """Initialize data for all symbols"""
        pass

    @abstractmethod
    def get_bars(
        self,
        symbol: str,
        lookback: int,
    ) -> List[Bar]:
        pass
