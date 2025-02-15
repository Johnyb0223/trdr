import asyncio
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

from trdr.core.bar_provider.yf_bar_provider import YFBarProvider
from trdr.core.broker.mock_broker import MockBroker
from trdr.core.strategy.strategy import Strategy

if __name__ == "__main__":

    async def main():
        tracer_provider = TracerProvider()
        otlp_exporter = OTLPSpanExporter(endpoint="localhost:4317", insecure=True)
        span_processor = BatchSpanProcessor(otlp_exporter, max_export_batch_size=20)
        tracer_provider.add_span_processor(span_processor)
        trace.set_tracer_provider(tracer_provider)
        tracer = trace.get_tracer("trdr")
        try:
            provider = await YFBarProvider.create(["AAPL"], tracer)
            async with await MockBroker.create(tracer=tracer) as broker:
                strategy = await Strategy.create("first-strat", broker, provider, tracer)
                print(strategy.strategy_ast)
                await strategy.execute()

        except Exception as e:
            print(e)

    asyncio.run(main())
