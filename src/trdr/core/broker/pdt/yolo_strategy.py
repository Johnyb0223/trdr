from trdr.core.broker.pdt.base_pdt_strategy import BasePDTStrategy


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

    def check_pdt_open_safely(self, number_of_positions_opened_today: int, rolling_day_trade_count: int) -> bool:
        return True

    def check_pdt_close_safely(self, position_opened_today: bool, rolling_day_trade_count: int) -> bool:
        return False
