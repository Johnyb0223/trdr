from typing import Optional
from opentelemetry import trace
from decimal import Decimal

from trdr.core.shared.models import Money
from trdr.core.portfolio.models import Position, Security, TradeContext, OrderSide
from trdr.core.portfolio.base_portfolio import BasePortfolio


class Portfolio(BasePortfolio):
    """Portfolio class for managing trading positions and orders.

    This class handles portfolio state including cash balance, positions, orders and trade tracking.
    It provides methods to check portfolio status and place trades while maintaining state.

    Attributes:
        _cash (Money): Current cash balance
        _open_positions (list[Position]): Currently open positions
        _open_orders (list[Order]): Currently open orders
        _rolling_day_trade_count (int): Number of day trades made today
        _last_refresh_time (TradingDateTime): Last time portfolio state was refreshed
        _broker (BaseBroker): Broker instance for executing trades
        _tracer (trace.Tracer): Opentracer tracer for monitoring

    Methods:
        create: Factory method to create new portfolio instance
        get_trade_context: Get current trading context for a security
        place_order: Place a new order
    """

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        """Disabled constructor - use Portfolio.create() instead."""
        raise TypeError("Use Portfolio.create() instead to create a new portfolio")

    async def _initialize(self):
        """Initialize portfolio state.

        Raises:
            PortfolioException: If initialization fails or required state is missing
        """
        with self._tracer.start_span("portfolio._initialize") as span:
            try:
                # Initialization logic placeholder
                span.add_event("initialize_portfolio")
                # ... any additional initialization steps
                pass
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.StatusCode.ERROR)
                raise
            else:
                span.set_status(trace.StatusCode.OK)

    async def _get_cash(self) -> Money:
        """Get current cash balance.

        Returns:
            Money: Current cash balance
        """
        with self._tracer.start_span("portfolio._get_cash") as span:
            span.add_event("get_cash")
            try:
                # Call get_cash only once and record the result as an attribute.
                cash = await self._broker.get_cash()
                span.set_attribute("cash", str(cash))
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.StatusCode.ERROR)
                raise
            else:
                span.set_status(trace.StatusCode.OK)
                return cash

    async def _get_equity(self) -> Money:
        """Calculate total portfolio equity.

        Returns:
            Money: Total portfolio value including cash and positions
        """
        with self._tracer.start_span("portfolio._get_equity") as span:
            try:
                equity = await self._broker.get_equity()
                span.set_attribute("equity", str(equity))
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.StatusCode.ERROR)
                raise
            else:
                span.set_status(trace.StatusCode.OK)
                return equity

    async def _get_position(self, security: Security) -> Optional[Position]:
        """Get the open position for a given security.

        Args:
            security: Security to check position for

        Returns:
            Optional[Position]: Position if found, None otherwise
        """
        with self._tracer.start_as_current_span("portfolio._get_position") as span:
            span.set_attribute("security", str(security))
            try:
                position = await self._broker.get_position(security)
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.StatusCode.ERROR)
                raise
            else:
                span.set_status(trace.StatusCode.OK)
                return position

    async def _get_account_exposure(self) -> Decimal:
        """Calculate total account exposure.

        Returns:
            Money: Total exposure as ratio of position cost to cash

        Example:
            returns 0.06 for a an account exposure of 6%. i.e, 6 percent of your account equity is tied up in open positions
        """
        with self._tracer.start_as_current_span("portfolio._get_account_exposure") as span:
            try:
                exposure = await self._broker.get_account_exposure()
                span.set_attribute("account_exposure", str(exposure))
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.StatusCode.ERROR)
                raise
            else:
                span.set_status(trace.StatusCode.OK)
                return exposure

    async def _get_position_exposure(self, security: Security) -> Optional[Money]:
        """Get exposure for a specific position.

        Args:
            security: Security to check exposure for

        Returns:
            Optional[Money]: Position exposure if position exists
        """
        with self._tracer.start_as_current_span("portfolio._get_position_exposure") as span:
            span.set_attribute("security", str(security))
            try:
                pos_exposure = await self._broker.get_position_exposure(security)
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.StatusCode.ERROR)
                raise
            else:
                span.set_status(trace.StatusCode.OK)
                return pos_exposure

    async def get_trade_context(self, security: Security) -> TradeContext:
        """Get current trading context for a security.

        Args:
            security: Security to get context for

        Returns:
            TradeContext: Current trading context
        """
        with self._tracer.start_as_current_span("portfolio.get_trade_context") as span:
            span.set_attribute("security", str(security))
            try:
                trade_context = TradeContext.model_validate(
                    {
                        "security": security,
                        "position": await self._get_position(security),
                        "cash": await self._get_cash(),
                        "equity": await self._get_equity(),
                        "account_exposure": await self._get_account_exposure(),
                        "position_exposure": await self._get_position_exposure(security),
                        "tracer": self._tracer,
                    }
                )
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.StatusCode.ERROR)
                raise
            else:
                span.set_status(trace.StatusCode.OK)
                return trade_context

    async def place_order(self, security: Security, side: OrderSide, dollar_amount: Money) -> None:
        """Place a new order.

        Args:
            security: Security to trade
            side: Whether to buy/long or sell/short
            dollar_amount: Dollar amount to trade
        """
        with self._tracer.start_as_current_span("portfolio.place_order") as span:
            span.set_attribute("security", str(security))
            span.set_attribute("side", str(side))
            span.set_attribute("dollar_amount", str(dollar_amount))
            try:
                await self._broker.place_order(security, side, dollar_amount)
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.StatusCode.ERROR)
                raise
            else:
                span.set_status(trace.StatusCode.OK)
