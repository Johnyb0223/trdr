from typing import List
from trdr.core.trading.portfolio import Portfolio
from trdr.core.strategy.strategy import Strategy
from trdr.core.data.interfaces import DataProvider
from trdr.core.trading.order_executor import OrderExecutor

class TradingEngine:
    def __init__(
        self,
        strategy: Strategy,
        data_provider: DataProvider,
        order_executor: OrderExecutor,
        portfolio: Portfolio,
        watchlist: List[str]
    ):
        self.strategy = strategy
        self.data_provider = data_provider
        self.order_executor = order_executor
        self.portfolio = portfolio
        self.watchlist = watchlist

    def process_trading_cycle(self):
        pass

    def _process_exits(self):
        """Check and execute exit conditions first"""
        pass
                
    
    def _process_entries(self):
        """Look for new entry opportunities"""
        pass