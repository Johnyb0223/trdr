# ALPACA Broker Implementation

The ALPACA broker implementation allows TRDR to connect with the Alpaca trading API for real and paper trading.

## Requirements

To use the ALPACA broker, you must set the following environment variables:

- `ALPACA_API_KEY`: Your Alpaca API key
- `ALPACA_SECRET_KEY`: Your Alpaca secret key
- `ALPACA_BASE_URL`: The Alpaca API base URL
  - For paper trading: `https://paper-api.alpaca.markets`
  - For live trading: `https://api.alpaca.markets`

## Important Notes

- The broker will automatically check if you're using a live trading URL and will display a warning if detected.
- Ensure your API keys have the appropriate permissions for the operations you intend to perform.
- The broker handles:
  - Account information retrieval
  - Position management
  - Order placement and cancellation
  - Pattern Day Trading (PDT) rule compliance through the PDT strategies

## Example Usage

```python
import asyncio
import os
from trdr.core.bar_provider.yf_bar_provider.yf_bar_provider import YFBarProvider
from trdr.core.security_provider.security_provider import SecurityProvider
from trdr.core.broker.alpaca_broker.alpaca_broker import AlpacaBroker
from trdr.core.trading_engine.trading_engine import TradingEngine
from trdr.core.trading_context.trading_context import TradingContext
from trdr.core.broker.pdt.nun_strategy import NunStrategy

# Set environment variables
os.environ["ALPACA_API_KEY"] = "your_api_key"
os.environ["ALPACA_SECRET_KEY"] = "your_secret_key"
os.environ["ALPACA_BASE_URL"] = "https://paper-api.alpaca.markets"  # For paper trading

async def main():
    try:
        pdt_strategy = NunStrategy.create()
        async with await AlpacaBroker.create(pdt_strategy=pdt_strategy) as broker:
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

## PDT Rule Compliance

The ALPACA broker works with TRDR's Pattern Day Trading rule compliance strategies. You can specify which PDT strategy to use when creating the broker:

```python
# Example with Nun Strategy
broker = await AlpacaBroker.create(pdt_strategy=NunStrategy.create())

# Example with YOLO Strategy
broker = await AlpacaBroker.create(pdt_strategy=YoloStrategy.create())
```