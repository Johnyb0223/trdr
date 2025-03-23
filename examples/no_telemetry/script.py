import asyncio

from trdr.core.bar_provider.yf_bar_provider.yf_bar_provider import YFBarProvider
from trdr.core.security_provider.security_provider import SecurityProvider
from trdr.core.broker.mock_broker.mock_broker import MockBroker
from trdr.core.trading_engine.trading_engine import TradingEngine
from trdr.core.trading_context.trading_context import TradingContext
from trdr.core.broker.pdt.nun_strategy import NunStrategy

if __name__ == "__main__":

    async def main():
        try:
            pdt_strategy = NunStrategy.create()
            async with await MockBroker.create(pdt_strategy=pdt_strategy) as broker:
                bar_provider = await YFBarProvider.create(["TSLA"])
                security_provider = await SecurityProvider.create(bar_provider)
                context = await TradingContext.create(security_provider, broker)
                engine = await TradingEngine.create("first-strat", context)
                await engine.execute()

        except Exception as e:
            print(e)

    asyncio.run(main())
