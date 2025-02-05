from typing import Union
from trdr.telemetry import TelemetryManager, NullTelemetryManager
from trdr.core.broker.pdt.base_pdt_strategy import BasePDTStrategy
from trdr.core.broker.pdt.interfaces import IPDTStrategy


class YoloStrategy(IPDTStrategy, BasePDTStrategy):
    """YOLO strategy - open positions without PDT constraints

    This strategy ignores PDT rules for opening positions but prevents same-day closes
    to avoid day trade counts. Very risky as positions can't be closed same day even
    if they move against you.
    """

    def __init__(self, telemetry: Union[TelemetryManager | NullTelemetryManager] = NullTelemetryManager()):
        super().__init__(telemetry)

    def check_pdt_open_safely(self, number_of_positions_opened_today: int, rolling_day_trade_count: int) -> bool:
        return True

    def check_pdt_close_safely(self, position_opened_today: bool, rolling_day_trade_count: int) -> bool:
        return False
