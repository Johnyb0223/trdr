from datetime import datetime
from decimal import Decimal
from typing import List
from trdr.core.trading.interfaces import IIndicator, IDataProvider
from trdr.core.data.bar import Bar
from trdr.core.strategy.logic import LogicalGroup, LogicalCondition
from trdr.core.strategy.strategy import Strategy
from stonks_shared.enums.timeframe import Timeframe
import operator

class MockDataProvider(IDataProvider):
    def get_bars(
        self, 
        symbol: str,
        timeframe: Timeframe,
        start: datetime,
        end: datetime
    ) -> List[Bar]:
        # Return some fake bars
        return [
            Bar(
                timestamp=datetime.now(),
                timeframe=Timeframe.D1,
                open=Decimal('100.00'),
                high=Decimal('105.00'),
                low=Decimal('95.00'),
                close=Decimal('102.00'),
                volume=1000000
            )
        ]

class MockMA20(IIndicator):
    def __init__(self, data_provider: IDataProvider):
        super().__init__(data_provider, Timeframe.D1)
        
    def value(self) -> float:
        return 100.0

class MockMA50(IIndicator):
    def __init__(self, data_provider: IDataProvider):
        super().__init__(data_provider, Timeframe.D1)
        
    def value(self) -> float:
        return 90.0

class MockRSI(IIndicator):
    def __init__(self, data_provider: IDataProvider):
        super().__init__(data_provider, Timeframe.D1)
        
    def value(self) -> float:
        return 25.0

class MockVolume(IIndicator):
    def __init__(self, data_provider: IDataProvider):
        super().__init__(data_provider, Timeframe.D1)
        
    def value(self) -> float:
        return 2000000.0

def test_first_strategy():
    # Setup
    data_provider = MockDataProvider()
    ma20 = MockMA20(data_provider)
    ma50 = MockMA50(data_provider)
    rsi = MockRSI(data_provider)
    volume = MockVolume(data_provider)
    
    # Create the strategy structure
    strategy = Strategy(
        name="First Strategy",
        description="Simple moving average crossover strategy"
    )
    
    # Build entry conditions
    entry = LogicalGroup('all_of')
    ma_conditions = LogicalGroup('any_of')
    ma_conditions.condition(LogicalCondition(ma20, operator.gt, ma50))
    ma_conditions.condition(LogicalCondition(ma20, operator.gt, 100.0))
    entry.expressions.append(ma_conditions)
    
    other_conditions = LogicalGroup('any_of')
    other_conditions.condition(LogicalCondition(rsi, operator.lt, 30.0))
    other_conditions.condition(LogicalCondition(volume, operator.gt, 1000000))
    entry.expressions.append(other_conditions)
    strategy.entry(entry)
    
    # Build exit conditions
    exit = LogicalGroup('all_of')
    exit.condition(LogicalCondition(ma20, operator.lt, ma50))
    strategy.exit(exit)
    
    # Build sizing conditions
    sizing = LogicalGroup('all_of')
    sizing.condition(LogicalCondition(volume, operator.gt, 0))  # Dummy condition for now
    strategy.sizing(sizing)
    
    # Test evaluation
    assert strategy.validate()
    assert strategy.entry_expression.evaluate() == True
