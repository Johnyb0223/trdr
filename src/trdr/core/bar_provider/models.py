from pydantic import BaseModel, model_validator

from ..shared.models import TradingDateTime, Money
from .exceptions import BarValidationException


class Bar(BaseModel):
    trading_datetime: TradingDateTime
    open: Money
    high: Money
    low: Money
    close: Money
    volume: int

    @model_validator(mode="after")
    def check_values(self) -> "Bar":
        # Validate that the low price is less than or equal to high price.
        if self.low.amount > self.high.amount:
            raise BarValidationException("Low price must be less than or equal to high price")
        # Validate that open price is between low and high.
        if not (self.low.amount <= self.open.amount <= self.high.amount):
            raise BarValidationException("Open price must be between low and high prices")
        # Validate that close price is between low and high.
        if not (self.low.amount <= self.close.amount <= self.high.amount):
            raise BarValidationException("Close price must be between low and high prices")
        # Validate that the volume is non-negative.
        if self.volume < 0:
            raise BarValidationException("Volume cannot be negative")
        return self

    def to_json(self) -> str:
        return self.model_dump_json(indent=2)

    def __str__(self) -> str:
        return (
            f"Bar(timestamp={self.trading_datetime}, open={self.open}, "
            f"high={self.high}, low={self.low}, close={self.close}, volume={self.volume})"
        )
