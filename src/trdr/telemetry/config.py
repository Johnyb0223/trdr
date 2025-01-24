from dataclasses import dataclass
from enum import Enum
from typing import Optional

class ExporterType(Enum):
    CONSOLE = "console"
    OTLP = "otlp"

@dataclass
class TelemetryConfig:
    """Configuration for OpenTelemetry instrumentation"""
    service_name: str = "trdr"
    enable_traces: bool = True
    enable_metrics: bool = True
    exporter_type: ExporterType = ExporterType.CONSOLE
    otlp_endpoint: Optional[str] = None