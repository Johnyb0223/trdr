# TRDR - Algorithmic Trading Framework

TRDR is a modular Python framework for creating, testing, and running algorithmic trading strategies with minimal code. It uses a domain-specific language (DSL) for defining trading strategies separate from execution logic.

## Features

- **Domain-Specific Language**: Define trading strategies with intuitive syntax in `.trdr` files
- **Modular Architecture**: Swap components (data providers, brokers) with minimal code changes
- **Asynchronous Operations**: Built on Python's async/await for efficient execution
- **Pattern Day Trading (PDT) Rule Support**: Built-in compliance with trading regulations
- **Observability**: OpenTelemetry integration for monitoring and tracing

## Core Components

### Bar Provider
Retrieves historical and real-time market data (OHLCV bars):
```python
bar_provider = await YFBarProvider.create(["AAPL", "MSFT"], tracer)
```

### Security Provider
Abstracts securities and their market data:
```python
security_provider = await SecurityProvider.create(bar_provider, tracer)
```

### Broker
Executes trades and manages account information:
```python
broker = await MockBroker.create(tracer=tracer)  # For testing
broker = await AlpacaBroker.create(api_key, api_secret, tracer)  # For live trading
```

### Strategy
Loads and executes trading strategies defined in DSL:
```python
strategy = await Strategy.create("my-strategy", broker, security_provider, tracer)
await strategy.execute()
```

## Strategy DSL

Strategies are defined in `.trdr` files with a clear syntax:

```
STRATEGY
    NAME "My Trading Strategy"
    DESCRIPTION "Buy when MA5 crosses above MA20, sell at profit target"
    
    ENTRY
        ALL_OF
            MA5 CROSSED_ABOVE MA20
            CURRENT_PRICE > 100
    
    EXIT
        ANY_OF
            CURRENT_PRICE > (AVERAGE_COST * 1.10)  # 10% profit
            CURRENT_PRICE < (AVERAGE_COST * 0.95)  # 5% stop loss
            
    SIZING
        RULE
            CONDITION
                AVAILABLE_CASH > 5000
            DOLLAR_AMOUNT 
                (AVAILABLE_CASH * 0.20)
```

## Getting Started

1. Install the package:
```bash
pip install trdr
```

2. Create a strategy file (my-strategy.trdr)

3. Run your strategy:
```python
import asyncio
from trdr.core.bar_provider.yf_bar_provider import YFBarProvider
from trdr.core.security_provider import SecurityProvider
from trdr.core.broker.mock_broker import MockBroker
from trdr.core.strategy import Strategy

async def main():
    # Initialize components
    bar_provider = await YFBarProvider.create(["AAPL"], None)
    broker = await MockBroker.create()
    security_provider = await SecurityProvider.create(bar_provider, None)
    
    # Load and execute strategy
    strategy = await Strategy.create("my-strategy", broker, security_provider, None)
    await strategy.execute()

asyncio.run(main())
```

See the `examples/` directory for complete examples.

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest
```

## Documentation

For more detailed information, see the following documentation:

- [Strategy DSL Reference](docs/DSL_REFERENCE.md) - How to write trading strategies in the TRDR DSL
- [Architecture Guide](docs/ARCHITECTURE.md) - Overview of the TRDR framework architecture