from abc import ABC, abstractmethod
from typing import Optional


class IPDTStrategy(ABC):
    """
    Abstract class for PDT strategies.
    """

    @abstractmethod
    def check_pdt_open_safely(self, number_of_positions_opened_today: int, rolling_day_trade_count: int) -> bool:
        """Determine if we can open a new position"""
        pass

    @abstractmethod
    def check_pdt_close_safely(self, position_opened_today: bool, rolling_day_trade_count: int) -> bool:
        """Determine if we can close an existing position"""
        pass
