from typing import List, Optional
from stonks_shared.enums.timeframe import Timeframe
from trdr.core.data.interfaces import IDataProvider, DataProviderError
from trdr.telemetry.config import TelemetryConfig
from trdr.telemetry.instrumentation import create_telemetry


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

    def __init__(
        self,
        symbols: List[str],
        timeframe: Timeframe = Timeframe.D1,
        telemetry_config: Optional[TelemetryConfig] = None,
    ):
        self._symbols = set(symbols)
        self._timeframe = timeframe
        self._data_cache = {}
        self._initialized = False
        self._telemetry = create_telemetry(telemetry_config)

    @classmethod
    async def create(
        cls,
        symbols: List[str],
        timeframe: Timeframe = Timeframe.D1,
        telemetry_config: Optional[TelemetryConfig] = None,
    ) -> "IDataProvider":
        """Factory method for creating and initializing provider"""
        if not symbols:
            raise DataProviderError("Symbols must be provided")
        provider = cls(symbols, timeframe, telemetry_config)
        await provider._initialize()
        return provider
