from .base_pdt_strategy import BasePDTStrategy
from .models import PDTContext, PDTDecision
from ..models import OrderSide, PositionSide


class WiggleStrategy(BasePDTStrategy):
    """Aggressive strategy - open positions with wiggle room

    This strategy allows opening more positions than available day trades:
    - With wiggle_room=2:
        - If 1 day trade used, can open 4 positions (2 can be closed same day)
        - If 0 day trades used, can open 5 positions (3 can be closed same day)

    The wiggle room translates to the number of positions opened that you would not be able to close same day
    """

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        """Disabled constructor - use WiggleStrategy.create() instead."""
        raise TypeError("Use WiggleStrategy.create() instead to create a new WiggleStrategy")

    def evaluate_order(self, context: PDTContext) -> PDTDecision:
        """
        Evaluate a proposed order against PDT rules with added wiggle room.

        This strategy allows opening more positions than standard PDT rules
        would normally permit, by increasing the maximum position count by
        the configured wiggle_room value.

        Args:
            context: PDT context with all relevant information

        Returns:
            PDTDecision with the evaluation result
        """

        number_of_positions_opened_today = context.count_of_positions_opened_today
        rolling_day_trade_count = context.rolling_day_trade_count

        if (
            (context.position is None)
            or (context.position.side == PositionSide.LONG and context.order.side == OrderSide.BUY)
            or (context.position.side == PositionSide.SHORT and context.order.side == OrderSide.SELL)
        ):
            # opening a new position
            max_positions = (3 - rolling_day_trade_count) + self.wiggle_room
            if number_of_positions_opened_today < max_positions:
                return PDTDecision(allowed=True, reason=f"Order allowed: within wiggle room (max={max_positions})")
            else:
                return PDTDecision(
                    allowed=False,
                    reason=f"PDT restrictions prevent opening a new position: exceeds wiggle room (max={max_positions})",
                )
        else:
            # check if we can close a position
            if rolling_day_trade_count < 3:
                return PDTDecision(allowed=True, reason="Order allowed: within wiggle room (max=3)")
            else:
                return PDTDecision(
                    allowed=False,
                    reason="PDT restrictions prevent closing a position: exceeds wiggle room (max=3)",
                )
