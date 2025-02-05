from typing import Union
from trdr.telemetry import TelemetryManager, NullTelemetryManager
from trdr.core.broker.pdt.base_pdt_strategy import BasePDTStrategy
from trdr.core.broker.pdt.interfaces import IPDTStrategy
from trdr.core.shared.exceptions import PDTStrategyException


class NunStrategy(IPDTStrategy, BasePDTStrategy):
    """Conservative strategy - only open positions we can safely close

    This strategy ensures we always have enough day trades available to close positions:
    - If we have 2 day trades used, we can only open 1 more position
    - If we have 1 day trade used, we can open 2 positions
    - If we have 0 day trades used, we can open 3 positions
    - results in us only being able to open 3 positions on any given day
    """

    def __init__(self, telemetry: Union[TelemetryManager | NullTelemetryManager] = NullTelemetryManager()):
        super().__init__(telemetry)

    def check_pdt_open_safely(self, number_of_positions_opened_today: int, rolling_day_trade_count: int) -> bool:
        """
        if we do not have an day trade available, we will not open a position
        """
        available_day_trades = 3 - rolling_day_trade_count
        return number_of_positions_opened_today < available_day_trades

    def check_pdt_close_safely(self, position_opened_today: bool, rolling_day_trade_count: int) -> bool:
        """
        this function should always return true as we should not have been able to open a position in the first place if we did not have a day trade availabe.

        raises:
        - PDTStrategyException: if we are not able to close a position. This should never happen as we should not have been able to open a position in the first place if we did not have a day trade availabe.
        """
        if not position_opened_today:
            return True
        if not rolling_day_trade_count < 3:
            raise PDTStrategyException(
                "We should never hit this condition as this strategy should always result in being able to close a position"
            )
        return True
