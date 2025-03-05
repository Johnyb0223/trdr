import pytest
import asyncio
from decimal import Decimal
from ..mock_broker.mock_broker import MockBroker
from ..models import OrderSide
from ...shared.models import Money
from .models import PDTContext, PDTDecision
from .exceptions import PDTRuleViolationException
from .nun_strategy import NunStrategy
from .wiggle_strategy import WiggleStrategy
from .yolo_strategy import YoloStrategy


# Test PDTContext and PDTDecision classes
def test_pdt_context_creation():
    """Test creating a PDTContext with different values."""
    context = PDTContext(
        symbol="AAPL",
        side=OrderSide.BUY,
        positions_opened_today=2,
        rolling_day_trade_count=1,
        position_opened_today=False,
        amount=Money(amount=Decimal(1000)),
    )

    assert context.symbol == "AAPL"
    assert context.side == OrderSide.BUY
    assert context.positions_opened_today == 2
    assert context.rolling_day_trade_count == 1
    assert context.position_opened_today is False
    assert context.amount == Money(amount=Decimal(1000))


def test_pdt_decision_creation():
    """Test creating a PDTDecision with different values."""
    decision = PDTDecision(allowed=True, reason="Test reason", modified_params={"amount": Money(amount=Decimal(500))})

    assert decision.allowed is True
    assert decision.reason == "Test reason"
    assert decision.modified_params == {"amount": Money(amount=Decimal(500))}


# Test NunStrategy with the new evaluate_order method
def test_nun_strategy_evaluate_buy_orders():
    """Test NunStrategy evaluating BUY orders with different contexts."""
    strategy = NunStrategy.create()

    # Test case: enough day trades available
    context = PDTContext(symbol="AAPL", side=OrderSide.BUY, positions_opened_today=1, rolling_day_trade_count=1)
    decision = strategy.evaluate_order(context)
    assert decision.allowed is True

    # Test case: not enough day trades available
    context = PDTContext(symbol="AAPL", side=OrderSide.BUY, positions_opened_today=2, rolling_day_trade_count=1)
    decision = strategy.evaluate_order(context)
    assert decision.allowed is False

    # Test case: no day trades left
    context = PDTContext(symbol="AAPL", side=OrderSide.BUY, positions_opened_today=0, rolling_day_trade_count=3)
    decision = strategy.evaluate_order(context)
    assert decision.allowed is False


def test_nun_strategy_evaluate_sell_orders():
    """Test NunStrategy evaluating SELL orders with different contexts."""
    strategy = NunStrategy.create()

    # Test case: position not opened today
    context = PDTContext(symbol="AAPL", side=OrderSide.SELL, position_opened_today=False, rolling_day_trade_count=3)
    decision = strategy.evaluate_order(context)
    assert decision.allowed is True

    # Test case: position opened today, day trades available
    context = PDTContext(symbol="AAPL", side=OrderSide.SELL, position_opened_today=True, rolling_day_trade_count=2)
    decision = strategy.evaluate_order(context)
    assert decision.allowed is True

    # Test case: position opened today, no day trades available
    context = PDTContext(symbol="AAPL", side=OrderSide.SELL, position_opened_today=True, rolling_day_trade_count=3)
    decision = strategy.evaluate_order(context)
    assert decision.allowed is False


# Test WiggleStrategy with the new evaluate_order method
def test_wiggle_strategy_evaluate_buy_orders():
    """Test WiggleStrategy evaluating BUY orders with different contexts."""
    strategy = WiggleStrategy.create()
    strategy.wiggle_room = 2

    # Test case: well within wiggle room limits
    context = PDTContext(symbol="AAPL", side=OrderSide.BUY, positions_opened_today=1, rolling_day_trade_count=1)
    decision = strategy.evaluate_order(context)
    assert decision.allowed is True

    # Test case: at wiggle room limit
    context = PDTContext(symbol="AAPL", side=OrderSide.BUY, positions_opened_today=3, rolling_day_trade_count=1)
    decision = strategy.evaluate_order(context)
    assert decision.allowed is True

    # Test case: exceeds wiggle room
    context = PDTContext(symbol="AAPL", side=OrderSide.BUY, positions_opened_today=4, rolling_day_trade_count=1)
    decision = strategy.evaluate_order(context)
    assert decision.allowed is False


# Test YoloStrategy with the new evaluate_order method
def test_yolo_strategy_evaluate_orders():
    """Test YoloStrategy evaluating orders with different contexts."""
    strategy = YoloStrategy.create()

    # Test case: buy order (always allowed)
    context = PDTContext(
        symbol="AAPL",
        side=OrderSide.BUY,
        positions_opened_today=10,  # Even with many positions
        rolling_day_trade_count=3,  # And all day trades used
    )
    decision = strategy.evaluate_order(context)
    assert decision.allowed is True

    # Test case: sell of position NOT opened today
    context = PDTContext(symbol="AAPL", side=OrderSide.SELL, position_opened_today=False, rolling_day_trade_count=3)
    decision = strategy.evaluate_order(context)
    assert decision.allowed is True

    # Test case: sell of position opened today (should be denied)
    context = PDTContext(
        symbol="AAPL",
        side=OrderSide.SELL,
        position_opened_today=True,
        rolling_day_trade_count=0,  # Even with day trades available
    )
    decision = strategy.evaluate_order(context)
    assert decision.allowed is False
