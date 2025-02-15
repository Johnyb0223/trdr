from typing import List

from .base_security_provider import BaseSecurityProvider
from .models import Security


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
        bars = await self._bar_provider.get_bars(symbol, 200)
        current_bar = await self._bar_provider.get_current_bar(symbol)
        return Security(symbol=symbol, bars=bars, current_bar=current_bar)

    async def get_security_list(self) -> List[Security]:
        symbols = self._bar_provider.get_symbols()
        return [await self.get_security(symbol) for symbol in symbols]
