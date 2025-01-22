from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List, Optional
from trdr.core.time.trading_datetime import TradingDateTime
from trdr.core.trading.models import Position


class Portfolio:
    def __init__(self, trading_api_client):
        self._api = trading_api_client
        self._positions: Dict[str, Position] = {}
        self._cash: Decimal = Decimal("0")
        self.refresh()  # Initial hydration
    
    def refresh(self) -> None:
        """Refresh portfolio state from broker API"""
        
        account = self._api.get_account()
        self._cash = Decimal(str(account.cash))
        
        
        api_positions = self._api.get_positions()
        self._positions.clear()
        
        for pos in api_positions:
            self._positions[pos.ticker] = Position(
                ticker=pos.ticker,
                quantity=Decimal(str(pos.quantity)),
                entry_price=Decimal(str(pos.entry_price)),
                entry_date=TradingDateTime.from_utc(pos.entry_date)
            )
    
    @property
    def cash(self) -> Decimal:
        return self._cash
    
    @property
    def open_positions(self) -> List[Position]:
        return list(self._positions.values())
    
    @property
    def total_value(self) -> Decimal:
        
        return self._api.get_account().portfolio_value
    
    def get_exposure(self) -> Decimal:
        """Returns total market exposure as a percentage of portfolio value"""
        if self.total_value == 0:
            return Decimal("0")
        return sum(p.market_value for p in self._positions.values()) / self.total_value
    
    def has_position(self, ticker: str) -> bool:
        return ticker in self._positions
    
    def get_position(self, ticker: str) -> Optional[Position]:
        return self._positions.get(ticker)
    
    # Note: We don't need add_position/remove_position methods anymore
    # because the OrderExecutor will handle trades and we'll refresh
    # the portfolio state after trades complete
    
    def update_position_prices(self) -> None:
        """Update latest prices from API"""
        self.refresh()  # Simplest approach is to just refresh everything
    
    def get_position_count(self) -> int:
        return len(self._positions)
    
    def get_position_weight(self, ticker: str) -> Decimal:
        """Get position weight as percentage of portfolio"""
        if ticker not in self._positions:
            return Decimal("0")
        return self._positions[ticker].market_value / self.total_value