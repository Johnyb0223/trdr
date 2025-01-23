from typing import List
from stonks_shared.enums.timeframe import Timeframe
from trdr.core.data.interfaces import IDataProvider, DataProviderError

class BaseDataProvider(IDataProvider):
    """Base implementation with common functionality

    properties:
        _symbols: List[str]
        _timeframe: Timeframe
        _data_cache: Dict[str, List[Bar]]
    
    methods:
        create: factory method that creates and initializes provider
        _initialize: asynchronous method that initializes data for all symbols
    """
    
    def __init__(self, symbols: List[str], timeframe: Timeframe = Timeframe.D1):
        if not symbols:
            raise DataProviderError("Symbols must be provided")
            
        self._symbols = set(symbols)
        self._timeframe = timeframe
        self._data_cache = {}

    @classmethod
    async def create(cls, symbols: List[str], timeframe: Timeframe = Timeframe.D1) -> 'IDataProvider':
        """Factory method for creating and initializing provider"""
        provider = cls(symbols, timeframe)
        await provider._initialize()
        return provider