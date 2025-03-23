from .base_pdt_strategy import BasePDTStrategy
from .models import PDTContext, PDTDecision
from ..models import OrderSide, PositionSide
from .exceptions import PDTStrategyException


class NunStrategy(BasePDTStrategy):
    """Pattern Day Trading (PDT) strategy that implements a conservative approach to position management.

    This strategy ensures compliance with PDT rules by maintaining enough day trades to safely close positions.
    The core logic reserves day trades for closing positions, limiting new position opens based on available
    day trades.

    Key Rules:
    - Maximum of 3 day trades per rolling window
    - New positions can only be opened if there are enough day trades reserved for closing
    - Position increases count as new positions for day trade purposes

    Attributes:
        Inherits all attributes from BasePDTStrategy
    """

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        """Disabled constructor - use NunStrategy.create() instead."""
        raise TypeError("Use NunStrategy.create() instead to create a new NunStrategy")

    def evaluate_order(self, context: PDTContext) -> PDTDecision:
        """Evaluates if a proposed order complies with PDT rules based on current trading context.

        The evaluation follows these steps:
        1. For new positions: checks if we have enough day trades reserved for closing
        2. For existing positions:
            - If increasing position: treats it like opening a new position
            - If closing position: always allowed since day trades were reserved

        Args:
            context (PDTContext): Contains current trading state including:
                - count_of_positions_opened_today: Number of new positions opened
                - rolling_day_trade_count: Number of day trades used in current window
                - position: Current position details if one exists
                - order: Proposed order details

        Returns:
            PDTDecision: Contains:
                - allowed: Boolean indicating if order is permitted
                - reason: String explaining the decision

        Raises:
            PDTStrategyException: If an unhandled case is encountered
        """

        number_of_positions_opened_today = context.count_of_positions_opened_today
        rolling_day_trade_count = context.rolling_day_trade_count

        # If we have no open position for order.symbol, we need to check if we can open a new position
        if context.position is None:
            if number_of_positions_opened_today + rolling_day_trade_count >= 3:
                return PDTDecision(
                    allowed=False,
                    reason="PDT restrictions prevent opening a new position: insufficient day trades available",
                )
            return PDTDecision(allowed=True, reason="Order allowed: sufficient day trades available")
        else:
            # if we are adding to a current position, we need to check if we can open a new position
            if (context.position.side == PositionSide.LONG and context.order.side == OrderSide.BUY) or (
                context.position.side == PositionSide.SHORT and context.order.side == OrderSide.SELL
            ):
                if number_of_positions_opened_today + rolling_day_trade_count >= 3:
                    return PDTDecision(
                        allowed=False,
                        reason="PDT restrictions prevent opening a new position: insufficient day trades available",
                    )
                return PDTDecision(allowed=True, reason="Order allowed: sufficient day trades available")
            elif (rolling_day_trade_count >= 3) and (
                (context.position.side == PositionSide.LONG and context.order.side == OrderSide.SELL)
                or (context.position.side == PositionSide.SHORT and context.order.side == OrderSide.BUY)
            ):
                raise PDTStrategyException(
                    f"We are trying to close a position with a current day trade count of 3. We should never reach this point as we should not have been able to open a new position in the first place. The NunStrategy should have prevented this from happening."
                )
            else:
                return PDTDecision(allowed=True, reason="Order allowed: sufficient day trades available")
