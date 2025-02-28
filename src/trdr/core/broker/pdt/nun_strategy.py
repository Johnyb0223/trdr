from .base_pdt_strategy import BasePDTStrategy
from .models import PDTContext, PDTDecision
from ..models import OrderSide


class NunStrategy(BasePDTStrategy):
    """Conservative strategy - only open positions we can safely close

    This strategy ensures we always have enough day trades available to close positions:
    - If we have 2 day trades used, we can only open 1 more position
    - If we have 1 day trade used, we can open 2 positions
    - If we have 0 day trades used, we can open 3 positions
    - results in us only being able to open 3 positions on any given day
    """

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        """Disabled constructor - use NunStrategy.create() instead."""
        raise TypeError("Use NunStrategy.create() instead to create a new NunStrategy")

    def evaluate_order(self, context: PDTContext) -> PDTDecision:
        """
        Evaluate a proposed order against PDT rules, ensuring we always have
        enough day trades available to close positions if needed.

        Args:
            context: PDT context with all relevant information

        Returns:
            PDTDecision with the evaluation result
        """
        if context.side == OrderSide.BUY:
            available_day_trades = 3 - context.rolling_day_trade_count
            if context.positions_opened_today < available_day_trades:
                return PDTDecision(allowed=True, reason="Order allowed: sufficient day trades available")
            else:
                return PDTDecision(
                    allowed=False,
                    reason="PDT restrictions prevent opening a new position: insufficient day trades available",
                )
        elif context.side == OrderSide.SELL:
            if not context.position_opened_today:
                # Not a day trade if position wasn't opened today
                return PDTDecision(allowed=True, reason="Order allowed: not a day trade")

            # If position was opened today, we need available day trades
            if context.rolling_day_trade_count < 3:
                return PDTDecision(allowed=True, reason="Order allowed: day trade available for position opened today")
            else:
                return PDTDecision(
                    allowed=False, reason="PDT restrictions prevent closing this position: no day trades available"
                )

        # Fallback for any other order types
        return PDTDecision(allowed=False, reason="Unknown order type")
