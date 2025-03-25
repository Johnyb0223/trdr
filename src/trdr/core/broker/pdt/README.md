# Pattern Day Trading (PDT) Strategies

This module provides different strategies for managing Pattern Day Trading (PDT) rule compliance. The PDT rule restricts traders with accounts under $25,000 to no more than 3 day trades in a 5 business day rolling period.

## Available Strategies

### NunStrategy

A conservative approach that prioritizes position safety:

- Reserves day trades for closing positions
- Ensures you can always close positions that need to be closed
- Prevents opening more positions than available day trades

```python
from trdr.core.broker.pdt.nun_strategy import NunStrategy

pdt_strategy = NunStrategy.create()
```

### WiggleStrategy

A balanced approach that provides flexibility:

- Allows opening more positions than available day trades (with "wiggle room")
- Can be configured with different wiggle room values
- With wiggle_room=2:
  - If 1 day trade used, can open 4 positions (2 can be closed same day)
  - If 0 day trades used, can open 5 positions (3 can be closed same day)

```python
from trdr.core.broker.pdt.wiggle_strategy import WiggleStrategy

pdt_strategy = WiggleStrategy.create()
```

### YoloStrategy

An aggressive approach:

- Allows unlimited opening of positions

```python
from trdr.core.broker.pdt.yolo_strategy import YoloStrategy

pdt_strategy = YoloStrategy.create()
```

## Implementing Custom Strategies

You can create your own PDT strategy by extending the `BasePDTStrategy` class:

```python
from trdr.core.broker.pdt.base_pdt_strategy import BasePDTStrategy
from trdr.core.broker.pdt.models import PDTContext, PDTDecision

class MyCustomStrategy(BasePDTStrategy):
    def evaluate_order(self, context: PDTContext) -> PDTDecision:
        # Implement your custom logic here
        return PDTDecision(allowed=True, reason="Custom logic allows this order")
```

## PDT Context

The `PDTContext` provides all necessary information for making PDT decisions:

- `count_of_positions_opened_today`: Number of new positions opened
- `rolling_day_trade_count`: Number of day trades used in current window
- `position`: Current position details if one exists
- `order`: Proposed order details

## Using PDT Strategies

When creating a broker instance, you can specify which PDT strategy to use:

```python
from trdr.core.broker.mock_broker.mock_broker import MockBroker
from trdr.core.broker.pdt.nun_strategy import NunStrategy

pdt_strategy = NunStrategy.create()
broker = await MockBroker.create(pdt_strategy=pdt_strategy)
```
