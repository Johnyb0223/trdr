import asyncio
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

from trdr.core.bar_provider.providers.yf_bar_provider import YFBarProvider
from trdr.core.portfolio.portfolio import Portfolio
from trdr.core.portfolio.models import Security
from trdr.core.broker.mock_broker import MockBroker

if __name__ == "__main__":

    async def main():
        tracer_provider = TracerProvider()
        span_processor = BatchSpanProcessor(ConsoleSpanExporter(service_name="trdr"))
        tracer_provider.add_span_processor(span_processor)
        trace.set_tracer_provider(tracer_provider)
        tracer = trace.get_tracer("python-opentelemetry-sdk")
        try:
            list_of_tickers = ["AAPL"]
            provider = await YFBarProvider.create(list_of_tickers, tracer)

            async with await MockBroker.create(tracer=tracer) as broker:
                portfolio = await Portfolio.create(broker=broker, tracer=tracer)

                for ticker in list_of_tickers:
                    current_bar = await provider.get_current_bar(ticker)
                    bars = await provider.get_bars(ticker, 1)
                    security = Security.model_validate(
                        {"symbol": ticker, "current_bar": current_bar, "bars": bars, "tracer": tracer}
                    )
                    trade_context = await portfolio.get_trade_context(security)
                    print(trade_context.to_json())

                positions = await broker.get_positions()
                print(positions)

        except Exception as e:
            print(e)

    asyncio.run(main())
