from .base_pdt_strategy import BasePDTStrategy
from .models import PDTContext, PDTDecision
from ..models import OrderSide


class WiggleStrategy(BasePDTStrategy):
    """Aggressive strategy - open positions with wiggle room

    This strategy allows opening more positions than available day trades:
    - With wiggle_room=2:
        - If 1 day trade used, can open 4 positions (2 can be closed same day)
        - If 0 day trades used, can open 5 positions (3 can be closed same day)
    """

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        """Disabled constructor - use WiggleStrategy.create() instead."""
        raise TypeError("Use WiggleStrategy.create() instead to create a new WiggleStrategy")

    @property
    def wiggle_room(self) -> int:
        """Get the wiggle room, with a default value if not set."""
        return getattr(self, "_wiggle_room", 2)  # Default wiggle room of 2

    @wiggle_room.setter
    def wiggle_room(self, value: int) -> None:
        """Set the wiggle room value."""
        self._wiggle_room = value

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
        if context.side == OrderSide.BUY:
            max_positions = (3 - context.rolling_day_trade_count) + self.wiggle_room
            if context.positions_opened_today < max_positions:
                return PDTDecision(allowed=True, reason=f"Order allowed: within wiggle room (max={max_positions})")
            else:
                return PDTDecision(
                    allowed=False,
                    reason=f"PDT restrictions prevent opening a new position: exceeds wiggle room (max={max_positions})",
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
