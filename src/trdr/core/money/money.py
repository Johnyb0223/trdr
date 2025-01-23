from decimal import Decimal
from dataclasses import dataclass
from typing import Union

@dataclass(frozen=True)
class Money:
    """Value object representing monetary amounts in trading context"""
    amount: Decimal
    currency: str = "USD"  # Default to USD since most trading is in dollars
    
    def __init__(self, amount: Union[str, Decimal, float], currency: str = "USD"):
        # Use object.__setattr__ since we're frozen
        object.__setattr__(self, 'amount', Decimal(str(amount)))
        object.__setattr__(self, 'currency', currency)
    
    def __add__(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError(f"Cannot add different currencies: {self.currency} and {other.currency}")
        return Money(self.amount + other.amount, self.currency)
    
    def __str__(self) -> str:
        return f"{self.currency} {self.amount:.2f}"