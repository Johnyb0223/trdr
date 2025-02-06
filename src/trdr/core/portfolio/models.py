from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, model_validator, Field
from opentelemetry import trace
from decimal import Decimal
from ..shared.models import Money, TradingDateTime
from ..bar_provider.models import Bar


class OrderStatus(Enum):
    """Represents the status of an order in the trading system.

    Values:
        PENDING: Order has been submitted but not yet executed
        FILLED: Order has been fully executed/filled
        CANCELLED: Order was cancelled before being filled
    """

    PENDING = "PENDING"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"

    def to_json(self) -> str:
        return self.value

    def __str__(self) -> str:
        return f"OrderStatus(value={self.value})"


class OrderSide(Enum):
    """Represents the side/direction of a trade or position.

    Values:
        BUY: Buy/long position
        SELL: Sell/short position
    """

    BUY = "BUY"
    SELL = "SELL"

    def to_json(self) -> str:
        return self.value


class Order(BaseModel):
    """Represents a trade order.

    Attributes:
        quantity: Number of shares/contracts to trade
        side: Whether to buy/long or sell/short
        status: Current status of the order
        timestamp: When the order was placed
    """

    quantity: Decimal
    side: OrderSide
    status: OrderStatus
    timestamp: TradingDateTime

    def to_json(self) -> str:
        return self.model_dump_json(indent=2)

    def __str__(self) -> str:
        return f"Order(quantity={self.quantity}, side={self.side}, status={self.status}, timestamp={self.timestamp})"

    class Config:
        arbitrary_types_allowed = True


class PositionSide(Enum):
    """Represents the side/direction of a trade or position.

    Values:
        LONG: Long/buy position
        SHORT: Short/sell position
    """

    LONG = "LONG"
    SHORT = "SHORT"

    def to_json(self) -> str:
        return self.value

    def __str__(self) -> str:
        return f"Side(value={self.value})"


class PositionStatus(Enum):
    """Represents the status of a position in the trading system.

    Values:
        OPEN: Position is open
        CLOSED: Position is closed
    """

    OPEN = "OPEN"
    CLOSED = "CLOSED"

    def to_json(self) -> str:
        return self.value


class Position(BaseModel):
    """Represents an open position in a security.

    Attributes:
        quantity: Number of shares/contracts held
        average_price: Average price per share/contract
        side: Whether position is long or short
    """

    symbol: str
    quantity: Decimal
    average_price: Money
    side: Optional[PositionSide]

    @classmethod
    def create_dummy_position(cls, symbol: str = "AAPL") -> "Position":
        return cls(
            symbol=symbol,
            quantity=10,
            average_price=Money(100, "USD"),
            side=PositionSide.LONG,
        )

    def to_json(self) -> str:
        return self.model_dump_json(indent=2)

    def __str__(self) -> str:
        return f"Position(quantity={self.quantity}, average_price={self.average_price}, side={self.side})"

    class Config:
        arbitrary_types_allowed = True


class Security(BaseModel):
    """A class representing a tradable security with price and volume data.

    Attributes:
        symbol (str): The ticker symbol for the security
        current_bar (Bar): The most recent price/volume bar
        bars (List[Bar]): Historical price/volume bars (minimum 200 required)
        tracer (Optional[trace.Tracer]): Opentracer tracer for monitoring

    Methods:
        validate_fields: Validates the security attributes
        get_current_price: Returns the current price
        get_X_day_moving_average: Returns X-day moving average price (X=5,20,50,100,200)
        get_X_day_average_volume: Returns X-day average volume (X=5,20,50,100,200)
    """

    symbol: str
    current_bar: Bar
    bars: List[Bar]
    tracer: Optional[trace.Tracer] = Field(default=trace.NoOpTracer(), exclude=True)

    def get_current_price(self) -> Money:
        """Returns the current price of the security.

        Returns:
            Money: The current price
        """
        return self.current_price

    def get_5_day_moving_average(self) -> Optional[Money]:
        """Calculates the 5-day moving average price.

        Returns:
            Money: The 5-day moving average price
        """
        if len(self.bars) < 5:
            return None
        sum_of_prices = sum(bar.close.amount for bar in self.bars[-5:])
        return Money(sum_of_prices / 5)

    def get_20_day_moving_average(self) -> Optional[Money]:
        """Calculates the 20-day moving average price.

        Returns:
            Money: The 20-day moving average price
        """
        if len(self.bars) < 20:
            return None
        sum_of_prices = sum(bar.close.amount for bar in self.bars[-20:])
        return Money(sum_of_prices / 20)

    def get_50_day_moving_average(self) -> Optional[Money]:
        """Calculates the 50-day moving average price.

        Returns:
            Money: The 50-day moving average price
        """
        if len(self.bars) < 50:
            return None
        sum_of_prices = sum(bar.close.amount for bar in self.bars[-50:])
        return Money(sum_of_prices / 50)

    def get_100_day_moving_average(self) -> Optional[Money]:
        """Calculates the 100-day moving average price.

        Returns:
            Money: The 100-day moving average price
        """
        if len(self.bars) < 100:
            return None
        sum_of_prices = sum(bar.close.amount for bar in self.bars[-100:])
        return Money(sum_of_prices / 100)

    def get_200_day_moving_average(self) -> Optional[Money]:
        """Calculates the 200-day moving average price.

        Returns:
            Money: The 200-day moving average price
        """
        if len(self.bars) < 200:
            return None
        sum_of_prices = sum(bar.close.amount for bar in self.bars[-200:])
        return Money(sum_of_prices / 200)

    def get_5_day_average_volume(self) -> Optional[Money]:
        """Calculates the 5-day average trading volume.

        Returns:
            Money: The 5-day average volume
        """
        if len(self.bars) < 5:
            return None
        sum_of_volumes = sum(bar.volume for bar in self.bars[-5:])
        return sum_of_volumes // 5

    def get_20_day_average_volume(self) -> Optional[Money]:
        """Calculates the 20-day average trading volume.

        Returns:
            Money: The 20-day average volume
        """
        if len(self.bars) < 20:
            return None
        sum_of_volumes = sum(bar.volume for bar in self.bars[-20:])
        return sum_of_volumes // 20

    def get_50_day_average_volume(self) -> Optional[Money]:
        """Calculates the 50-day average trading volume.

        Returns:
            Money: The 50-day average volume
        """
        if len(self.bars) < 50:
            return None
        sum_of_volumes = sum(bar.volume for bar in self.bars[-50:])
        return sum_of_volumes // 50

    def get_100_day_average_volume(self) -> Optional[Money]:
        """Calculates the 100-day average trading volume.

        Returns:
            Money: The 100-day average volume
        """
        if len(self.bars) < 100:
            return None
        sum_of_volumes = sum(bar.volume for bar in self.bars[-100:])
        return sum_of_volumes // 100

    def get_200_day_average_volume(self) -> Optional[Money]:
        """Calculates the 200-day average trading volume.

        Returns:
            Money: The 200-day average volume
        """
        if len(self.bars) < 200:
            return None
        sum_of_volumes = sum(bar.volume for bar in self.bars[-200:])
        return sum_of_volumes // 200

    @model_validator(mode="after")
    def validate_fields(cls, values):
        """Validates the security fields.

        Checks:
        - Symbol is a string
        - Bars is a list with at least 200 entries
        - Current bar is a valid Bar object

        Args:
            values: The model instance being validated

        Returns:
            The validated model instance

        Raises:
            ValueError: If any validation checks fail
        """
        tracer = values.tracer
        bars = values.bars
        current_bar = values.current_bar
        symbol = values.symbol

        with tracer.start_as_current_span("Security.validate_fields") as span:
            # Validate symbol
            if not isinstance(symbol, str):
                span.set_status(trace.StatusCode.ERROR)
                span.record_exception(ValueError("Symbol must be a string"))
                raise ValueError("Symbol must be a string")
            span.set_attribute("symbol", symbol)
            span.add_event("symbol_validated")
            # Validate bars
            if not isinstance(bars, list):
                span.set_status(trace.StatusCode.ERROR)
                span.record_exception(ValueError("Bars must be a list"))
                raise ValueError("Bars must be a list")
            span.add_event("bars_validated")

            # Validate current_bar
            if not isinstance(current_bar, Bar):
                span.set_status(trace.StatusCode.ERROR)
                span.record_exception(ValueError("Current bar must be a Bar object"))
                raise ValueError("Current bar must be a Bar object")
            span.add_event("current_bar_validated")

            span.set_status(trace.StatusCode.OK)
            span.add_event("security_validated")

        return values

    @classmethod
    def create_dummy_security(cls, symbol: str = "AAPL") -> "Security":
        bars = Bar.create_dummy_bars(count=200)
        return cls(
            symbol=symbol,
            current_bar=bars[-2],
            bars=bars,
        )

    def to_json(self) -> str:
        return self.model_dump_json(exclude={"tracer"}, indent=2)

    def __str__(self) -> str:
        """Returns a string representation of the Security.

        Returns:
            str: String containing symbol, current bar, moving averages and volumes
        """
        return (
            f"Security(symbol={self.symbol}, "
            f"current_bar={self.current_bar}, "
            f"bars_count={len(self.bars)}, "
            f"5_day_moving_average={self.get_5_day_moving_average()}, "
            f"20_day_moving_average={self.get_20_day_moving_average()}, "
            f"50_day_moving_average={self.get_50_day_moving_average()}, "
            f"200_day_moving_average={self.get_200_day_moving_average()}, "
            f"5_day_average_volume={self.get_5_day_average_volume()}, "
            f"20_day_average_volume={self.get_20_day_average_volume()}, "
            f"50_day_average_volume={self.get_50_day_average_volume()}, "
            f"100_day_average_volume={self.get_100_day_average_volume()}, "
            f"200_day_average_volume={self.get_200_day_average_volume()})"
        )

    class Config:
        arbitrary_types_allowed = True


class TradeContext(BaseModel):
    """
    Represents the trading context with details about the security, current position,
    cash, equity, and exposures within an account.

    Attributes:
        security (Security): The security being traded.
        position (Optional[Position]): The current open position for the security, if any.
        cash (Money): Cash available in the account.
        equity (Money): Account equity, representing cash plus the market value of positions.
        rolling_day_trade_count (int): Number of day trades executed over a rolling five-day period.
        account_exposure (Decimal): Total account exposure, representing the overall allocation risk.
        position_exposure (Optional[Decimal]): Exposure of the position as a fraction of account equity.
            Must be set if a position exists; otherwise, it should remain unset.
    """

    # the security we are trading
    security: Security
    # position we have open for the current security
    position: Optional[Position]
    # the cash we have in our account
    cash: Money
    # account equity (cash + position value)
    equity: Money

    # account exposure
    account_exposure: Decimal
    # position exposure as a ratio of account equity
    position_exposure: Optional[Decimal]

    # tracer
    tracer: Optional[trace.Tracer] = Field(default=trace.NoOpTracer(), exclude=True)

    @model_validator(mode="after")
    def mutually_inclusive_position_and_position_exposure(cls, values):
        """
        Validates that position and position_exposure fields are mutually inclusive.

        If a position exists, position_exposure must be set.
        If no position exists, position_exposure must not be set.

        Args:
            values: The model instance being validated

        Returns:
            The validated model instance

        Raises:
            ValueError: If validation fails due to mismatched position/exposure values
        """
        tracer = values.tracer

        with tracer.start_as_current_span("TradeContext.mutually_inclusive_position_and_position_exposure") as span:
            position = values.position
            position_exposure = values.position_exposure
            if position is not None and position_exposure is None:
                span.set_status(trace.StatusCode.ERROR)
                span.record_exception(ValueError("Position exposure cannot be None if position is set"))
                raise ValueError("Position exposure cannot be None if position is set")
            if position is None and position_exposure is not None:
                span.set_status(trace.StatusCode.ERROR)
                span.record_exception(ValueError("Position exposure cannot be set if position is not set"))
                raise ValueError("Position exposure cannot be set if position is not set")
            span.set_status(trace.StatusCode.OK)
            span.add_event("mutually_inclusive_position_and_position_exposure_validated")
        return values

    def to_json(self) -> str:
        return self.model_dump_json(indent=2)

    def __str__(self) -> str:
        return f"TradeContext(security={self.security}, position={self.position}, cash={self.cash}, equity={self.equity}, account_exposure={self.account_exposure}, position_exposure={self.position_exposure})"

    class Config:
        arbitrary_types_allowed = True
