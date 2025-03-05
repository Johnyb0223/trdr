from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from ..broker.models import Position
from ..shared.models import Money


class MissingContextValue(Exception):
    def __init__(self, message: str):
        self.message = message

    def __str__(self) -> str:
        return self.message


class ContextIdentifier(str, Enum):
    MA5 = "ma5"
    MA20 = "ma20"
    MA50 = "ma50"
    MA100 = "ma100"
    MA200 = "ma200"
    AV5 = "av5"
    AV20 = "av20"
    AV50 = "av50"
    AV100 = "av100"
    AV200 = "av200"
    CURRENT_VOLUME = "current_volume"
    ACCOUNT_EXPOSURE = "account_exposure"
    OPEN_POSITIONS = "open_positions"
    AVAILABLE_CASH = "available_cash"
    STOCK_VALUE = "stock_value"
    CURRENT_PRICE = "current_price"
    AVG_COST = "avg_cost"
    CURRENT_POSITION = "current_position"
    AVERAGE_COST = "average_cost"


class StrategyContext(BaseModel):
    ma5: Optional[Money] = Field(None, description="5-day moving average")
    ma20: Optional[Money] = Field(None, description="20-day moving average")
    ma50: Optional[Money] = Field(None, description="50-day moving average")
    ma100: Optional[Money] = Field(None, description="100-day moving average")
    ma200: Optional[Money] = Field(None, description="200-day moving average")
    av5: Optional[int] = Field(None, description="5-day average volume")
    av20: Optional[int] = Field(None, description="20-day average volume")
    av50: Optional[int] = Field(None, description="50-day average volume")
    av100: Optional[int] = Field(None, description="100-day average volume")
    av200: Optional[int] = Field(None, description="200-day average volume")
    current_volume: Optional[int] = Field(None, description="Current trading volume")
    account_exposure: Optional[float] = Field(None, description="Account exposure percentage")
    open_positions: Optional[int] = Field(None, description="Number of open positions")
    available_cash: Optional[Money] = Field(None, description="Available cash")
    stock_value: Optional[Money] = Field(None, description="Stock value")
    current_price: Optional[Money] = Field(None, description="Current price")
    average_cost: Optional[Money] = Field(None, description="Average position price")

    model_config = ConfigDict(arbitrary_types_allowed=True)
