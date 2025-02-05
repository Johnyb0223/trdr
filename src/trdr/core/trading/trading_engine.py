from typing import List, Optional
from trdr.core.portfolio.base_portfolio import IPortfolio
from trdr.core.strategy.strategy import Strategy
from trdr.core.bar_provider.interfaces import IDataProvider
from trdr.telemetry import TelemetryConfig
from trdr.telemetry.instrumentation import create_telemetry
from trdr.core.shared.exceptions import DataProviderException, PortfolioException


class TradingEngine:
    def __init__(
        self,
        strategy: Strategy,
        data_provider: IDataProvider,
        portfolio: IPortfolio,
        watchlist: List[str],
        telemetry_config: Optional[TelemetryConfig] = None,
    ):
        self.strategy = strategy
        self.data_provider = data_provider
        self.portfolio = portfolio
        self.watchlist = watchlist
        self._telemetry = create_telemetry(telemetry_config)

    @classmethod
    async def create(
        cls,
        strategy: Strategy,
        data_provider: IDataProvider,
        portfolio: IPortfolio,
        watchlist: List[str],
        telemetry_config: Optional[TelemetryConfig] = None,
    ):
        provider = cls(strategy, data_provider, portfolio, watchlist, telemetry_config)
        await provider._initialize()
        return provider

    async def _initialize(self):
        if not self.data_provider._initialized:
            raise DataProviderException("Data provider is not initialized")
        if not self.portfolio._initialized:
            raise PortfolioException("Portfolio is not initialized")

    def process_trading_cycle(self):
        pass

    def _process_exits(self):
        """Check and execute exit conditions first"""
        pass

    def _process_entries(self):
        """Look for new entry opportunities"""
        pass
