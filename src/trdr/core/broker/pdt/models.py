from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict

from ...shared.models import Money
from ..models import OrderSide


class PDTContext(BaseModel):
    """
    Contains all the information needed by PDT strategies to make decisions.

    This context object encapsulates broker state and order information,
    allowing PDT strategies to make informed decisions about whether to
    allow trading actions.
    """

    # Order information
    symbol: str
    side: OrderSide
    amount: Optional[Money] = None

    # Account state
    positions_opened_today: int = 0
    rolling_day_trade_count: int = 0
    position_opened_today: bool = False  # For the specific symbol in the order

    # Additional information
    equity: Optional[Money] = None
    broker_name: Optional[str] = None
    broker_specific_data: Dict[str, Any] = {}

    model_config = ConfigDict(arbitrary_types_allowed=True)


class PDTDecision(BaseModel):
    """
    The decision made by a PDT strategy about a proposed trading action.

    This includes whether the action is allowed, the reason for the decision,
    and any suggested modifications to the order parameters.
    """

    allowed: bool = False
    reason: Optional[str] = None
    modified_params: Dict[str, Any] = {}

    model_config = ConfigDict(arbitrary_types_allowed=True)
