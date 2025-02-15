from pydantic import BaseModel, model_validator

import random
from datetime import timedelta
from typing import List, Optional
from decimal import Decimal
from opentelemetry import trace
from pydantic import Field


from ..shared.models import TradingDateTime, Money, Timeframe
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

    @classmethod
    def create_dummy_bars(cls, count: int, start_price: Money = Money(100)) -> List["Bar"]:
        bars = []
        current_price = start_price
        current_datetime = TradingDateTime.now()

        for _ in range(count):
            open_p = current_price.amount
            # A small random movement to simulate market changes
            price_change = Decimal(random.gauss(0, 1))  # mean=0, std=1
            close_p = open_p + price_change

            # Generate high and low values that surround open and close.
            high_p = max(open_p, close_p) + Decimal(random.gauss(0, 0.5))
            low_p = min(open_p, close_p) - Decimal(random.gauss(0, 0.5))

            # Simulate volume with random variation.
            volume = random.randint(800, 1200)

            bar = cls(
                trading_datetime=current_datetime,
                open=Money(open_p),
                high=Money(high_p),
                low=Money(low_p),
                close=Money(close_p),
                volume=volume,
            )

            bars.append(bar)

            # Prepare for the next iteration: use the current close as the next open.
            current_price = Money(close_p)
            # Increment the timestamp (here we add 1 minute between bars).
            current_datetime = current_datetime + timedelta(minutes=1)

        return bars

    def to_json(self) -> str:
        return self.model_dump_json(indent=2)

    def __str__(self) -> str:
        return (
            f"Bar(timestamp={self.trading_datetime}, open={self.open}, "
            f"high={self.high}, low={self.low}, close={self.close}, volume={self.volume})"
        )



