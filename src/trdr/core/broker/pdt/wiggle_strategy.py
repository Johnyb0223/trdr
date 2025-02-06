from typing import Union
from trdr.core.broker.pdt.base_pdt_strategy import BasePDTStrategy


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

    def check_pdt_open_safely(self, number_of_positions_opened_today: int, rolling_day_trade_count: int) -> bool:
        max_positions = (3 - rolling_day_trade_count) + self.wiggle_room
        return number_of_positions_opened_today < max_positions

    def check_pdt_close_safely(self, position_opened_today: bool, rolling_day_trade_count: int) -> bool:
        if not position_opened_today:
            return True
        return rolling_day_trade_count < 3
