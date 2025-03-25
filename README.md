# TRDR - Trading Framework

TRDR is a framework for algorithmic trading in Python. It features a custom Domain-Specific Language (DSL) for expressing trading strategies in a clear, concise manner.

## 🌟 Features

- **Custom DSL**: Define trading strategies with a readable, declarative syntax
- **Modular Architecture**: Easily swap components like brokers and data providers
- **Async First**: Built from the ground up with Python's async/await pattern
- **Mock Trading**: Test strategies with a mock broker before using real money
- **Telemetry Integration**: Optional OpenTelemetry support for performance monitoring
- **Pattern Day Trading Controls**: Built-in [PDT rule compliance strategies](src/trdr/core/broker/pdt/README.md) (NunStrategy, WiggleStrategy, YoloStrategy)

## 📦 Installation

```bash
# Basic installation
pip install trdr

# Development installation (with testing tools)
pip install -e ".[dev]"
```

## 🚀 Quick Start

### 1. Define Your Strategy

Create a file `my-strategy.trdr` with your trading strategy:

```
STRATEGY
    NAME "Moving Average Crossover"
    DESCRIPTION "Basic MA crossover strategy with risk management"
    ENTRY
        ALL_OF
            MA5 CROSSED_ABOVE MA20
            MA20 > MA50
            CURRENT_PRICE > 100
    EXIT
        ANY_OF
            CURRENT_PRICE > (AVERAGE_COST * 1.06)  # 6% profit target
            CURRENT_PRICE < (AVERAGE_COST * 0.98)  # 2% stop loss
    SIZING
        RULE
            CONDITION
                ALL_OF
                    ACCOUNT_EXPOSURE < 0.5
                    NUMBER_OF_OPEN_POSITIONS < 3
            DOLLAR_AMOUNT 
                (AVAILABLE_CASH * 0.20)
```

### 2. Run Your Strategy

```python
import asyncio
from trdr.core.bar_provider.yf_bar_provider.yf_bar_provider import YFBarProvider
from trdr.core.security_provider.security_provider import SecurityProvider
from trdr.core.broker.mock_broker.mock_broker import MockBroker
from trdr.core.trading_engine.trading_engine import TradingEngine
from trdr.core.trading_context.trading_context import TradingContext
from trdr.core.broker.pdt.nun_strategy import NunStrategy

async def main():
    try:
        pdt_strategy = NunStrategy.create()
        async with await MockBroker.create(pdt_strategy=pdt_strategy) as broker:
            bar_provider = await YFBarProvider.create(["TSLA"])
            security_provider = await SecurityProvider.create(bar_provider)
            context = await TradingContext.create(security_provider, broker)
            engine = await TradingEngine.create("my-strategy", context)
            await engine.execute()
    except Exception as e:
        print(e)

if __name__ == "__main__":
    asyncio.run(main())
```

## 🛠️ Architecture

TRDR is built with a modular, component-based architecture:

- **Bar Provider**: Supplies price/volume data (Yahoo Finance implementation included)
- **Security Provider**: Manages available securities for trading
- **Broker**: Handles order execution
  - [Mock Broker](src/trdr/core/broker/mock_broker/) - Local simulation for testing
  - [Alpaca Broker](src/trdr/core/broker/alpaca_broker/README.md) - Real trading with Alpaca API
- **Trading Context**: Coordinates components and maintains state
- **Trading Engine**: Executes strategies using the DSL parser
- **[PDT Strategies](src/trdr/core/broker/pdt/README.md)**: Enforces Pattern Day Trading rules with multiple compliance strategies

## 📊 DSL Reference

The TRDR Domain Specific Language provides a clean syntax for expressing trading logic:

### Strategy Structure

```
STRATEGY
    NAME "Strategy Name"
    DESCRIPTION "Strategy Description"
    ENTRY
        # Entry conditions
    EXIT
        # Exit conditions
    SIZING
        # Position sizing rules
```

### Logical Operators

```
ALL_OF          # All conditions must be true
ANY_OF          # Any condition can be true
```

### Technical Indicators

```
MA{period}      # Moving average (e.g., MA5, MA20, MA50, MA100, MA200)
AV{period}      # Average volume (e.g., AV5, AV20, AV50, AV100, AV200)
```

### Comparison Operators

```
>               # Greater than
<               # Less than
>=              # Greater than or equal to
<=              # Less than or equal to
==              # Equal to
CROSSED_ABOVE   # Indicator crossed above another
CROSSED_BELOW   # Indicator crossed below another
```

### Price Metrics

```
CURRENT_PRICE   # Current price of the security
CURRENT_VOLUME  # Current volume of the security
```

### Account Metrics

```
ACCOUNT_EXPOSURE        # Percentage of account exposed to market
AVAILABLE_CASH          # Available cash for trading
AVERAGE_COST            # Average cost of current position
NUMBER_OF_OPEN_POSITIONS # Number of currently open positions
```

### Mathematical Operators

```
+               # Addition
-               # Subtraction
*               # Multiplication
/               # Division
(expression)    # Parentheses for grouping expressions
```

## 📚 Examples

Check the `examples/` directory for complete examples:

- **No Telemetry Example**: Basic usage without OpenTelemetry
- **With Telemetry Example**: Using OpenTelemetry for monitoring
- **Strategy Examples**: Sample trading strategies

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest src/trdr/path/to/test_file.py

# Run specific test
pytest src/trdr/path/to/test_file.py::TestClass::test_method
```

## 📝 License

[MIT License](LICENSE)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
