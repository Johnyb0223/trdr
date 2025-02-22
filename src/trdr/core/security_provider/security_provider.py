from typing import List
from opentelemetry import trace

from .base_security_provider import BaseSecurityProvider
from .models import Security
from ..bar_provider.exceptions import InsufficientBarsException, NoBarsForSymbolException


class SecurityProvider(BaseSecurityProvider):
    def __init__(
        self,
        *args,
        **kwargs,
    ):
        """Disabled constructor - use SecurityProvider.create() instead."""
        raise TypeError("Use SecurityProvider.create() instead to create a new security provider")

    async def _initialize(self) -> None:
        pass

    async def get_security(self, symbol: str) -> Security:
        with self._tracer.start_as_current_span("SecurityProvider.get_security") as span:
            span.set_attribute("symbol", symbol)
            try:
                bars = await self._bar_provider.get_bars(symbol)
                current_bar = await self._bar_provider.get_current_bar(symbol)
            except (InsufficientBarsException, NoBarsForSymbolException) as e:
                span.set_status(trace.StatusCode.OK)
                span.add_event("No bars found for symbol", {"symbol": symbol})
                return None
            except Exception as e:
                span.set_status(trace.StatusCode.ERROR)
                span.record_exception(e)
                raise e
            else:
                span.set_status(trace.StatusCode.OK)
                return Security(symbol=symbol, bars=bars, current_bar=current_bar)

    async def get_security_list(self) -> List[Security]:
        with self._tracer.start_as_current_span("SecurityProvider.get_security_list") as span:
            symbols = self._bar_provider.get_symbols()
            list_of_security_objects = [await self.get_security(symbol) for symbol in symbols]
            span.set_status(trace.StatusCode.OK)
            return list_of_security_objects
