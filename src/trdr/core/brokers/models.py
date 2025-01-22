from dataclasses import dataclass
from decimal import Decimal
from trdr.core.time.trading_datetime import TradingDateTime

@dataclass
class APIAccountInfo:
    """Value object representing account information"""
    cash: Decimal
    portfolio_value: Decimal
    buying_power: Decimal
    currency: str = "USD"

@dataclass
class APIPosition:
    """Value object representing position information from API"""
    ticker: str
    quantity: Decimal
    entry_price: Decimal
    entry_date: TradingDateTime
    current_price: Decimal
    
@dataclass
class APIOrderResult:
    """Value object representing order execution result"""
    order_id: str
    ticker: str
    side: str  # "BUY" or "SELL"
    quantity: Decimal
    fill_price: Decimal
    fill_time: TradingDateTime
    status: str  # "FILLED", "PARTIAL", "REJECTED", etc.