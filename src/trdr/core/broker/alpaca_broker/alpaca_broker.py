from typing import Optional
import os
from opentelemetry import trace
from opentelemetry.trace import NoOpTracer

from ..base_broker import BaseBroker
from ..exceptions import BrokerInitializationException, BrokerException
from ...shared.models import Money, TradingDateTime
from ..models import OrderSide
from ..pdt.base_pdt_strategy import BasePDTStrategy
from ..pdt.nun_strategy import NunStrategy


class AlpacaBroker(BaseBroker):
    def __init__(self, *args, **kwargs):
        raise TypeError("Use AlpacaBroker.create() instead")

    @classmethod
    async def create(
        cls,
        alpaca_api_key: Optional[str] = None,
        alpaca_secret_key: Optional[str] = None,
        base_url: Optional[str] = None,
        pdt_strategy: Optional[BasePDTStrategy] = None,
        tracer: trace.Tracer = NoOpTracer(),
    ) -> "AlpacaBroker":
        self = cls.__new__(cls)
        if pdt_strategy is None:
            pdt_strategy = NunStrategy()
        BaseBroker.__init__(self, pdt_strategy=pdt_strategy, tracer=tracer)
        self._alpaca_api_key = alpaca_api_key or os.getenv("ALPACA_API_KEY")
        self._alpaca_secret_key = alpaca_secret_key or os.getenv("ALPACA_SECRET_KEY")
        self._alpaca_base_url = base_url or os.getenv("ALPACA_BASE_URL")
        with self._tracer.start_as_current_span("AlpacaBroker.create") as span:
            try:
                await self._initialize()
                await self._refresh()
                self._updated_dt = TradingDateTime.now()
                self._is_state_in_good_order()
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.StatusCode.ERROR)
                raise
            else:
                span.set_status(trace.StatusCode.OK)
        return self

    async def _initialize(self):
        with self._tracer.start_as_current_span("AlpacaBroker._initialize") as span:
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
                        error_detail = await response.text()
                        raise BrokerInitializationException(
                            f"Failed to connect to Alpaca API: {response.status}, {error_detail}"
                        )
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.StatusCode.ERROR)
                raise e
            else:
                span.set_status(trace.StatusCode.OK)

    async def _refresh(self) -> None:
        with self._tracer.start_as_current_span("AlpacaBroker._refresh") as span:
            try:
                async with self._session.get(f"{self._alpaca_base_url}/v2/account") as response:
                    if response.status != 200:
                        error_detail = await response.text()
                        raise BrokerException(f"Alpaca API error: {response.status} - {error_detail}")
                    data = await response.json()
                    cash = data.get("cash")
                    if cash is None:
                        raise BrokerException("Cash not found in API response")
                    self._cash = Money(cash)
                    equity = data.get("equity")
                    if equity is None:
                        raise BrokerException("Equity not found in API response")
                    self._equity = Money(equity)
                    # For simplicity, positions and day trade count are set with dummy values.
                    self._positions = {}
                    self._day_trade_count = 0
                    span.set_status(trace.StatusCode.OK)
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.StatusCode.ERROR)
                raise e

    async def _place_order(self, symbol: str, side: OrderSide, dollar_amount: Money) -> None:
        with self._tracer.start_as_current_span("AlpacaBroker._place_order") as span:
            try:
                # TODO: Implement actual Alpaca order placement logic via API.
                span.add_event(f"Placing order for {symbol}: side={side}, dollar_amount={dollar_amount}")
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.StatusCode.ERROR)
                raise e
            else:
                span.set_status(trace.StatusCode.OK)
