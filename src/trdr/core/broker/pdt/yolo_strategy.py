from .base_pdt_strategy import BasePDTStrategy
from .models import PDTContext, PDTDecision
from ..models import OrderSide


class YoloStrategy(BasePDTStrategy):
    """YOLO strategy - open positions without PDT constraints

    This strategy ignores PDT rules for opening positions but prevents same-day closes
    to avoid day trade counts. Very risky as positions can't be closed same day even
    if they move against you.
    """

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        """Disabled constructor - use YoloStrategy.create() instead."""
        raise TypeError("Use YoloStrategy.create() instead to create a new YoloStrategy")

    def evaluate_order(self, context: PDTContext) -> PDTDecision:
        """
        Evaluate a proposed order for the YOLO strategy.

        This strategy allows unlimited opening of positions but prevents
        closing any position that was opened today to avoid day trade counts.

        Args:
            context: PDT context with all relevant information

        Returns:
            PDTDecision with the evaluation result
        """
        if context.side == OrderSide.BUY:
            # Always allow buying
            return PDTDecision(allowed=True, reason="Order allowed: YOLO strategy permits unlimited buys")
        elif context.side == OrderSide.SELL:
            if not context.position_opened_today:
                # Only allow selling if position wasn't opened today
                return PDTDecision(allowed=True, reason="Order allowed: position not opened today")
            else:
                # Never allow same-day sells
                return PDTDecision(allowed=False, reason="Cannot sell position opened today under YOLO strategy")

        # Fallback for any other order types
        return PDTDecision(allowed=False, reason="Unknown order type")
