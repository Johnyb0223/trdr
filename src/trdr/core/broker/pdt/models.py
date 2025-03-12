from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict


from ..models import Position, Order


class PDTContext(BaseModel):
    """
    Contains all the information needed by PDT strategies to make decisions.

    This context object encapsulates broker state and order information,
    allowing PDT strategies to make informed decisions about whether to
    allow trading actions.
    """

    # Order information
    order: Order
    position: Optional[Position] = None

    # Account state
    count_of_positions_opened_today: int = 0
    rolling_day_trade_count: int = 0

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
