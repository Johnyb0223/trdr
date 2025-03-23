import pytest
from decimal import Decimal

from ..models import OrderSide
from ...shared.models import Money
from .models import PDTContext, PDTDecision
from .nun_strategy import NunStrategy
from .wiggle_strategy import WiggleStrategy
from .yolo_strategy import YoloStrategy


def test_pdt_context_creation(create_order, long_dummy_position):
    order = create_order(long_dummy_position.symbol, side=OrderSide.BUY)

    context = PDTContext(
        position=long_dummy_position,
        order=order,
        count_of_positions_opened_today=2,
        rolling_day_trade_count=1,
    )

    assert context.position.symbol == long_dummy_position.symbol
    assert context.order.side == OrderSide.BUY
    assert context.count_of_positions_opened_today == 2
    assert context.rolling_day_trade_count == 1
    assert context.order == order


def test_pdt_decision_creation():
    """Test creating a PDTDecision with different values."""
    decision = PDTDecision(allowed=True, reason="Test reason", modified_params={"amount": Money(amount=Decimal(500))})

    assert decision.allowed is True
    assert decision.reason == "Test reason"
    assert decision.modified_params == {"amount": Money(amount=Decimal(500))}


# Test NunStrategy with the new evaluate_order method
def test_nun_strategy_evaluate_new_position(create_order):
    """Test NunStrategy evaluating orders for new positions."""
    strategy = NunStrategy.create()

    # Test case: opening new position with sufficient day trades
    order = create_order("AAPL", side=OrderSide.BUY)
    context = PDTContext(position=None, order=order, count_of_positions_opened_today=1, rolling_day_trade_count=1)
    decision = strategy.evaluate_order(context)
    assert decision.allowed is True

    # Test case: opening new position with insufficient day trades
    context = PDTContext(position=None, order=order, count_of_positions_opened_today=2, rolling_day_trade_count=1)
    decision = strategy.evaluate_order(context)
    assert decision.allowed is False

    # Test case: no day trades left
    context = PDTContext(position=None, order=order, count_of_positions_opened_today=0, rolling_day_trade_count=3)
    decision = strategy.evaluate_order(context)
    assert decision.allowed is False


def test_nun_strategy_evaluate_existing_position(create_order, long_dummy_position, short_dummy_position):
    """Test NunStrategy evaluating orders for existing positions."""
    strategy = NunStrategy.create()

    # Test case: adding to existing long position with sufficient day trades
    buy_order = create_order(long_dummy_position.symbol, side=OrderSide.BUY)
    context = PDTContext(
        position=long_dummy_position, order=buy_order, count_of_positions_opened_today=1, rolling_day_trade_count=1
    )
    decision = strategy.evaluate_order(context)
    assert decision.allowed is True

    # Test case: adding to existing long position with insufficient day trades
    context = PDTContext(
        position=long_dummy_position, order=buy_order, count_of_positions_opened_today=2, rolling_day_trade_count=1
    )
    decision = strategy.evaluate_order(context)
    assert decision.allowed is False

    # Test case: Add to existing short position with sufficient day trades
    sell_order = create_order(short_dummy_position.symbol, side=OrderSide.SELL)
    context = PDTContext(
        position=short_dummy_position, order=sell_order, count_of_positions_opened_today=2, rolling_day_trade_count=0
    )
    decision = strategy.evaluate_order(context)
    assert decision.allowed is True

    # Test case: Add to existing short position with insufficient day trades
    context = PDTContext(
        position=short_dummy_position, order=sell_order, count_of_positions_opened_today=2, rolling_day_trade_count=1
    )
    decision = strategy.evaluate_order(context)
    assert decision.allowed is False


# Test WiggleStrategy with the new evaluate_order method
def test_wiggle_strategy_evaluate_new_position(create_order):
    """Test WiggleStrategy evaluating new position orders with different contexts."""
    strategy = WiggleStrategy.create()
    strategy.wiggle_room = 2

    # Test case: well within wiggle room limits (1 used day trade, can open 4 positions)
    order = create_order("AAPL", side=OrderSide.BUY)
    context = PDTContext(position=None, order=order, count_of_positions_opened_today=0, rolling_day_trade_count=1)
    decision = strategy.evaluate_order(context)
    assert decision.allowed is True

    # Test case: at wiggle room limit (1 used day trade, max 4 positions)
    context = PDTContext(position=None, order=order, count_of_positions_opened_today=4, rolling_day_trade_count=0)
    decision = strategy.evaluate_order(context)
    assert decision.allowed is True

    # Test case: exceeds wiggle room
    context = PDTContext(position=None, order=order, count_of_positions_opened_today=5, rolling_day_trade_count=1)
    decision = strategy.evaluate_order(context)
    assert decision.allowed is False

    # Test case: 0 day trades used - can open more positions
    context = PDTContext(position=None, order=order, count_of_positions_opened_today=4, rolling_day_trade_count=0)
    decision = strategy.evaluate_order(context)
    assert decision.allowed is True

    # Test case: all day trades used - can only open wiggle_room positions
    context = PDTContext(position=None, order=order, count_of_positions_opened_today=1, rolling_day_trade_count=3)
    decision = strategy.evaluate_order(context)
    assert decision.allowed is True

    # Test case: all day trades used, at wiggle room limit
    context = PDTContext(position=None, order=order, count_of_positions_opened_today=2, rolling_day_trade_count=3)
    decision = strategy.evaluate_order(context)
    assert decision.allowed is False


def test_wiggle_strategy_evaluate_existing_position(create_order, long_dummy_position, short_dummy_position):
    """Test WiggleStrategy evaluating orders for existing positions."""
    strategy = WiggleStrategy.create()
    strategy.wiggle_room = 2

    # Test case: closing long position with day trades available
    sell_order = create_order(long_dummy_position.symbol, side=OrderSide.SELL)
    context = PDTContext(
        position=long_dummy_position, order=sell_order, count_of_positions_opened_today=1, rolling_day_trade_count=2
    )
    decision = strategy.evaluate_order(context)
    assert decision.allowed is True

    # Test case: closing long position with no day trades available
    context = PDTContext(
        position=long_dummy_position, order=sell_order, count_of_positions_opened_today=1, rolling_day_trade_count=3
    )
    decision = strategy.evaluate_order(context)
    assert decision.allowed is False

    # Test case: adding to existing long position (treated as new position)
    buy_order = create_order(long_dummy_position.symbol, side=OrderSide.BUY)
    context = PDTContext(
        position=long_dummy_position, order=buy_order, count_of_positions_opened_today=4, rolling_day_trade_count=1
    )
    decision = strategy.evaluate_order(context)
    assert decision.allowed is False

    # Test case: closing short position with day trades available
    buy_order = create_order(short_dummy_position.symbol, side=OrderSide.BUY)
    context = PDTContext(
        position=short_dummy_position, order=buy_order, count_of_positions_opened_today=1, rolling_day_trade_count=2
    )
    decision = strategy.evaluate_order(context)
    assert decision.allowed is True

    # Test case: closing short position with no day trades available
    buy_order = create_order(short_dummy_position.symbol, side=OrderSide.BUY)
    context = PDTContext(
        position=short_dummy_position, order=buy_order, count_of_positions_opened_today=1, rolling_day_trade_count=3
    )
    decision = strategy.evaluate_order(context)
    assert decision.allowed is False


# Test YoloStrategy with the new evaluate_order method
def test_yolo_strategy_evaluate_new_position(create_order):
    """Test YoloStrategy evaluating new position orders."""
    strategy = YoloStrategy.create()

    # Test case: new buy order with many positions open and all day trades used
    buy_order = create_order("AAPL", side=OrderSide.BUY)
    context = PDTContext(
        position=None,
        order=buy_order,
        count_of_positions_opened_today=10,  # Even with many positions
        rolling_day_trade_count=3,  # And all day trades used
    )
    decision = strategy.evaluate_order(context)
    assert decision.allowed is True
    assert "YOLO strategy permits unlimited buys" in decision.reason

    # Test case: adding to existing long position (treated as opening a new position)
    context = PDTContext(
        position=None,  # Here we simulate the position being None for the YOLO check
        order=buy_order,
        count_of_positions_opened_today=20,  # Very high number of positions
        rolling_day_trade_count=3,  # All day trades used
    )
    decision = strategy.evaluate_order(context)
    assert decision.allowed is True
    assert "YOLO strategy permits unlimited buys" in decision.reason


def test_yolo_strategy_evaluate_existing_position(create_order, long_dummy_position, short_dummy_position):
    """Test YoloStrategy evaluating orders for existing positions."""
    strategy = YoloStrategy.create()

    # Test case: closing long position with day trades available
    sell_order = create_order(long_dummy_position.symbol, side=OrderSide.SELL)
    context = PDTContext(
        position=long_dummy_position, order=sell_order, count_of_positions_opened_today=1, rolling_day_trade_count=2
    )
    decision = strategy.evaluate_order(context)
    assert decision.allowed is True
    assert "YOLO strategy permits unlimited sells" in decision.reason

    # Test case: closing long position with no day trades available
    context = PDTContext(
        position=long_dummy_position,
        order=sell_order,
        count_of_positions_opened_today=1,
        rolling_day_trade_count=3,  # No day trades available
    )
    decision = strategy.evaluate_order(context)
    assert decision.allowed is False
    assert "YOLO strategy prevents same-day closes" in decision.reason

    # Test case: closing short position with day trades available
    buy_order = create_order(short_dummy_position.symbol, side=OrderSide.BUY)
    context = PDTContext(
        position=short_dummy_position, order=buy_order, count_of_positions_opened_today=1, rolling_day_trade_count=2
    )
    decision = strategy.evaluate_order(context)
    assert decision.allowed is True

    # Test case: closing short position with no day trades available
    context = PDTContext(
        position=short_dummy_position,
        order=buy_order,
        count_of_positions_opened_today=1,
        rolling_day_trade_count=3,  # No day trades available
    )
    decision = strategy.evaluate_order(context)
    assert decision.allowed is False
