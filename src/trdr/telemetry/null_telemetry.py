from contextlib import contextmanager
from typing import Optional, Generator


class NullSpan:
    def set_attribute(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def set_status(self, *args, **kwargs):
        pass

    def record_exception(self, *args, **kwargs):
        pass

    def add_event(self, *args, **kwargs):
        pass


class NullTelemetryManager:
    """No-op implementation when telemetry is not enabled/installed"""

    @contextmanager
    def span(self, name: str) -> Generator[Optional[NullSpan], None, None]:
        yield NullSpan()
