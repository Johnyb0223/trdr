from typing import Optional, List, Union
import os
import asyncio
from opentelemetry import trace
from opentelemetry.trace import NoOpTracer

from trdr.core.broker.base_broker import AsyncBaseBroker
from trdr.core.shared.exceptions import BrokerInitializationException, BrokerException
from trdr.core.shared.models import Money, Position, Order
from trdr.core.broker.pdt.interfaces import IPDTStrategy
from trdr.core.broker.pdt.nun_strategy import NunStrategy


class AlpacaBroker(AsyncBaseBroker):
    """Broker implementation for the Alpaca trading platform.

    Provides an interface to interact with the Alpaca trading API for executing trades,
    managing positions, and accessing account information.

    The broker can be configured with API credentials either directly or via environment variables:
    - ALPACA_API_KEY: Your Alpaca API key
    - ALPACA_SECRET_KEY: Your Alpaca secret key
    - ALPACA_BASE_URL: The Alpaca API endpoint URL

    The base URL must match your environment:
    - Paper trading: https://paper-api.alpaca.markets
    - Live trading: https://api.alpaca.markets

    Attributes:
        _alpaca_api_key (str): API key for authentication
        _alpaca_secret_key (str): Secret key for authentication
        _alpaca_base_url (str): Base URL for API endpoints
        _pdt_strategy (IPDTStrategy): Strategy for Pattern Day Trading rule compliance
        _session (aiohttp.ClientSession): HTTP session for API requests
        _tracer (TelemetryManager): tracer manager for instrumentation
    """

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        """Disabled constructor - use AlpacaBroker.create() instead."""
        raise TypeError("Use AlpacaBroker.create() instead")

    @classmethod
    async def create(
        cls,
        alpaca_api_key: Optional[str] = None,
        alpaca_secret_key: Optional[str] = None,
        base_url: Optional[str] = None,
        pdt_strategy: IPDTStrategy = NunStrategy(),
        tracer: trace.Tracer = NoOpTracer(),
    ):
        """Create and initialize an AlpacaBroker instance.

        Args:
            alpaca_api_key: API key for authentication. Falls back to ALPACA_API_KEY env var.
            alpaca_secret_key: Secret key for authentication. Falls back to ALPACA_SECRET_KEY env var.
            base_url: Base URL for API endpoints. Falls back to ALPACA_BASE_URL env var.
            pdt_strategy: Strategy for Pattern Day Trading rule compliance.
            tracer: tracer manager for instrumentation.

        Returns:
            AlpacaBroker: Initialized broker instance.

        Example:
            ```python
            broker = await AlpacaBroker.create(
                alpaca_api_key="your_key",
                alpaca_secret_key="your_secret",
                base_url="https://paper-api.alpaca.markets",
                pdt_strategy=NunStrategy(),
                tracer=tracerManager(),
            )
            ```
        """
        self = cls.__new__(cls)
        AsyncBaseBroker.__init__(self, tracer=tracer)
        self._alpaca_api_key = alpaca_api_key or os.getenv("ALPACA_API_KEY")
        self._alpaca_secret_key = alpaca_secret_key or os.getenv("ALPACA_SECRET_KEY")
        self._alpaca_base_url = base_url or os.getenv("ALPACA_BASE_URL")
        self._pdt_strategy = pdt_strategy
        await self._initialize()
        return self

    async def _initialize(self):
        """Initialize the Alpaca broker by validating credentials and testing API connectivity.

        Validates that required API credentials are provided and tests the connection
        by making a request to the account endpoint.

        Raises:
            BrokerInitializationException: If API credentials are missing or API connection fails
        """
        if not self._alpaca_api_key or not self._alpaca_secret_key:
            raise BrokerInitializationException("Alpaca API key and secret key are required")
        if not self._alpaca_base_url:
            raise BrokerInitializationException("Base URL is required")

        self._session.headers.update(
            {
                "APCA-API-KEY-ID": self._alpaca_api_key,
                "APCA-API-SECRET-KEY": self._alpaca_secret_key,
            }
        )

        try:
            async with self._session.get(f"{self._alpaca_base_url}/v2/account") as response:
                if response.status != 200:
                    raise BrokerInitializationException(
                        f"Failed to connect to Alpaca API: {response.status}, {response.text}"
                    )
        except Exception as e:
            raise e

    async def get_cash(self) -> Money:
        """Get available cash balance from Alpaca account.

        Returns:
            Money: Available cash balance

        Raises:
            BrokerException: If API request fails or response is invalid
        """
        try:
            async with self._session.get(f"{self._alpaca_base_url}/v2/account") as response:
                if response.status != 200:
                    error_detail = await response.text()
                    raise BrokerException(f"Alpaca API error: {response.status} - {error_detail}")
                data = await response.json()
                cash = data.get("cash")
                if not cash:
                    raise BrokerException("Cash not found in API response")
                return Money(cash)
        except Exception as e:
            raise e

    async def get_open_positions(self) -> List[Position]:
        """Get all current open positions.

        Returns:
            List[Position]: List of open positions
        """
        pass

    async def get_open_orders(self) -> List[Order]:
        """Get all pending orders.

        Returns:
            List[Order]: List of pending orders
        """
        pass


if __name__ == "__main__":

    async def main():
        async with await AlpacaBroker.create() as broker:
            cash = await broker.get_cash()
            print(cash)

    asyncio.run(main())
