from typing import List
from decimal import Decimal
import random
import datetime
from pydantic import BaseModel, ConfigDict
from typing import Literal

from ..core.bar_provider.models import Bar
from ..core.shared.models import Money, TradingDateTime, Timeframe
from ..core.security_provider.models import Security


class MovingAverage(BaseModel):
    timeframe: Timeframe
    target: Decimal
    operator: Literal["==", ">", "<"]


class Crossover(BaseModel):
    type: Literal["golden_cross", "death_cross"]
    ma1: Timeframe
    ma2: Timeframe


class SecurityCriteria(BaseModel):
    bar_count: int
    start_price: Money | None = Money(amount=Decimal(random.randint(10, 500)))
    start_volume: int | None = random.randint(1000, 100000)
    moving_averages: List[MovingAverage] | None = None
    crossovers: List[Crossover] | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)


class SecurityGenerator:
    def __init__(self, criteria: SecurityCriteria):
        self.criteria = criteria

    def create_dummy_bars(self, count: int, start_price: Money, start_volume: int) -> List["Bar"]:
        bars = []
        current_price = start_price
        base_datetime = datetime.datetime.now(datetime.UTC)
        while base_datetime.date().weekday() >= 5:
            if base_datetime.date().weekday() == 5:
                base_datetime = base_datetime + datetime.timedelta(days=2)
            else:
                base_datetime = base_datetime + datetime.timedelta(days=1)
        current_datetime = TradingDateTime.from_utc(base_datetime)

        trend_shift_probability = 0.05
        trend_range = (-0.2, 0.2)
        trend = Decimal(random.uniform(*trend_range))

        for _ in range(count):
            open_p = current_price.amount
            price_change = trend + Decimal(random.gauss(0, 1.5))
            price_change = max(price_change, -open_p * Decimal("0.1"))
            close_p = max(open_p + price_change, open_p * Decimal("0.5"))

            daily_volatility = abs(close_p - open_p) * Decimal("0.5")
            low_p = min(open_p, close_p) - abs(Decimal(random.gauss(0, 0.5))) * daily_volatility
            high_p = max(open_p, close_p) + abs(Decimal(random.gauss(0, 0.5))) * daily_volatility

            low_p = max(low_p, open_p * Decimal("0.9"))
            if low_p > high_p:
                low_p, high_p = high_p, low_p

            volume = max(100, int(start_volume * random.gauss(1, 0.3)))

            bar = Bar(
                trading_datetime=current_datetime,
                open=Money(amount=Decimal(open_p)),
                high=Money(amount=Decimal(high_p)),
                low=Money(amount=Decimal(low_p)),
                close=Money(amount=Decimal(close_p)),
                volume=volume,
            )

            bars.append(bar)
            current_price = Money(amount=Decimal(close_p))

            if random.random() < trend_shift_probability:
                trend = Decimal(random.uniform(*trend_range))

            base_datetime = current_datetime.timestamp
            while True:
                if base_datetime.date().weekday() == 5:
                    base_datetime = base_datetime + datetime.timedelta(days=2)
                else:
                    base_datetime = base_datetime + datetime.timedelta(days=1)
                if base_datetime.date().weekday() < 5:
                    current_datetime = TradingDateTime.from_utc(base_datetime)
                    break

        return bars

    def find_suitable_security(self) -> "Security":
        while True:
            bars = self.create_dummy_bars(
                self.criteria.bar_count, self.criteria.start_price, self.criteria.start_volume
            )
            security = Security(symbol="AAPL", current_bar=bars[0], bars=bars)

            if self.evaluate_security(security):
                return security

    def evaluate_security(self, security: "Security") -> bool:
        if self.criteria.moving_averages:
            for condition in self.criteria.moving_averages:
                timeframe = condition.timeframe
                target = condition.target
                operator = condition.operator

                computed_ma = security.compute_moving_average(timeframe)
                if not self.evaluate_criteria(computed_ma.amount, target, operator):
                    return False

        if self.criteria.crossovers:
            for crossover in self.criteria.crossovers:
                ma1_current = security.compute_moving_average(crossover.ma1)
                ma2_current = security.compute_moving_average(crossover.ma2)
                ma1_previous = security.compute_moving_average(crossover.ma1, 1)
                ma2_previous = security.compute_moving_average(crossover.ma2, 1)

                if not self.evaluate_crossover(
                    ma1_previous.amount, ma2_previous.amount, ma1_current.amount, ma2_current.amount, crossover.type
                ):
                    return False

        return True

    def evaluate_criteria(self, value, target, operator):
        if operator == "==":
            return abs(value - target) <= Decimal("0.2")
        elif operator == ">":
            return value > target
        elif operator == "<":
            return value < target
        return False

    def evaluate_crossover(self, ma1_prev, ma2_prev, ma1_curr, ma2_curr, crossover_type):
        if crossover_type == "golden_cross":
            return ma1_prev < ma2_prev and ma1_curr > ma2_curr
        elif crossover_type == "death_cross":
            return ma1_prev > ma2_prev and ma1_curr < ma2_curr
        return False


if __name__ == "__main__":
    criteria = SecurityCriteria(
        bar_count=100,
        moving_averages=[MovingAverage(timeframe=Timeframe.d5, target=Decimal(100), operator=">")],
        crossovers=[Crossover(type="golden_cross", ma1=Timeframe.d5, ma2=Timeframe.d20)],
    )
    generator = SecurityGenerator(criteria)
    security = generator.find_suitable_security()
    ma5 = security.compute_moving_average(Timeframe.d5)
    ma5_prev = security.compute_moving_average(Timeframe.d5, 1)
    ma20 = security.compute_moving_average(Timeframe.d20)
    ma20_prev = security.compute_moving_average(Timeframe.d20, 1)
    print(f"Current - ma5: {ma5}, ma20: {ma20}")
    print(f"Previous - ma5: {ma5_prev}, ma20: {ma20_prev}")
