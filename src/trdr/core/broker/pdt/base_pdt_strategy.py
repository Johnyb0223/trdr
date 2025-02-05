from typing import Union
from trdr.telemetry import TelemetryManager, NullTelemetryManager
from trdr.core.broker.pdt.interfaces import IPDTStrategy


class BasePDTStrategy:
    def __init__(self, telemetry: Union[TelemetryManager | NullTelemetryManager] = NullTelemetryManager()):
        self._telemetry = telemetry
