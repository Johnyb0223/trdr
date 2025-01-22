from abc import ABC, abstractmethod
from typing import List
from decimal import Decimal
from trdr.core.brokers.models import APIAccountInfo, APIPosition, APIOrderResult

class TradingAPIClient(ABC):
    """Abstract interface for broker API interactions"""
    
    @abstractmethod
    def get_account(self) -> APIAccountInfo:
        """Get current account information"""
        pass
    
    @abstractmethod
    def get_positions(self) -> List[APIPosition]:
        """Get all current positions"""
        pass
    
    @abstractmethod
    def place_order(
        self, 
        ticker: str, 
        side: str,
        quantity: Decimal,
        order_type: str = "MARKET"  # or "LIMIT"
    ) -> APIOrderResult:
        """Place a trade order"""
        pass
    
    @abstractmethod
    def is_market_open(self) -> bool:
        """Check if market is currently open"""
        pass