from contextlib import contextmanager
from typing import Optional, Generator, Union
from enum import Enum
from trdr.telemetry.config import TelemetryConfig, ExporterType
from trdr.telemetry.null_telemetry import NullTelemetryManager


class StatusCode(Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


class Status:
    def __init__(self, code: StatusCode, description: str = None):
        self.code = code
        self.description = description


class TelemetryManager:
    def __init__(self, config: TelemetryConfig):
        self.config = config
        self._tracer = None

        if not self._has_telemetry_packages():
            return

        if self.config.enable_traces:
            self._setup_tracing()

    def _has_telemetry_packages(self) -> bool:
        try:
            import opentelemetry.trace

            return True
        except ImportError:
            return False

    def _setup_tracing(self) -> None:
        # Import OpenTelemetry packages only when needed
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import (
            BatchSpanProcessor,
            ConsoleSpanExporter,
        )
        from opentelemetry.sdk.resources import Resource

        resource = Resource.create({"service.name": self.config.service_name})
        provider = TracerProvider(resource=resource)

        # Set up the appropriate exporter based on configuration
        if self.config.exporter_type == ExporterType.CONSOLE:
            exporter = ConsoleSpanExporter()
        elif self.config.exporter_type == ExporterType.OTLP:
            if not self.config.otlp_endpoint:
                raise ValueError("OTLP endpoint must be specified when using OTLP exporter")
            raise NotImplementedError("OTLP exporter is not implemented")
        else:
            raise ValueError(f"Unsupported exporter type: {self.config.exporter_type}")

        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
        self._tracer = trace.get_tracer(__name__)

    @contextmanager
    def span(self, name: str) -> Generator[Optional["Span"], None, None]:
        """
        Context manager for creating spans if tracing is enabled
        """
        if not self._tracer:
            yield None
            return

        with self._tracer.start_as_current_span(name) as span:
            yield span


def create_telemetry(config: Optional[TelemetryConfig] = None) -> Union[TelemetryManager, NullTelemetryManager]:
    """Factory function to create appropriate telemetry manager"""
    if config is None:
        return NullTelemetryManager()

    try:
        return TelemetryManager(config)
    except ImportError:
        return NullTelemetryManager()
