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

    # Test case: closing existing long position (always allowed)
    sell_order = create_order(long_dummy_position.symbol, side=OrderSide.SELL)
    context = PDTContext(
        position=long_dummy_position, order=sell_order, count_of_positions_opened_today=2, rolling_day_trade_count=3
    )
    decision = strategy.evaluate_order(context)
    assert decision.allowed is True

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
def test_wiggle_strategy_evaluate_buy_orders(create_order):
    """Test WiggleStrategy evaluating BUY orders with different contexts."""
    strategy = WiggleStrategy.create()
    strategy.wiggle_room = 2

    # Test case: well within wiggle room limits
    order = create_order("AAPL", side=OrderSide.BUY)
    context = PDTContext(position=None, order=order, count_of_positions_opened_today=1, rolling_day_trade_count=1)
    decision = strategy.evaluate_order(context)
    assert decision.allowed is True

    # Test case: at wiggle room limit
    context = PDTContext(position=None, order=order, count_of_positions_opened_today=3, rolling_day_trade_count=1)
    decision = strategy.evaluate_order(context)
    assert decision.allowed is True

    # Test case: exceeds wiggle room
    context = PDTContext(position=None, order=order, count_of_positions_opened_today=4, rolling_day_trade_count=1)
    decision = strategy.evaluate_order(context)
    assert decision.allowed is False


# Test YoloStrategy with the new evaluate_order method
def test_yolo_strategy_evaluate_orders(create_order, long_dummy_position):
    """Test YoloStrategy evaluating orders with different contexts."""
    strategy = YoloStrategy.create()

    # Test case: buy order (always allowed)
    buy_order = create_order("AAPL", side=OrderSide.BUY)
    context = PDTContext(
        position=None,
        order=buy_order,
        count_of_positions_opened_today=10,  # Even with many positions
        rolling_day_trade_count=3,  # And all day trades used
    )
    decision = strategy.evaluate_order(context)
    assert decision.allowed is True

    # Test case: sell of position NOT opened today
    # We'll need to modify the context with appropriate position data
    sell_order = create_order(long_dummy_position.symbol, side=OrderSide.SELL)

    # For testing selling a position not opened today, we'd need to setup the position properly
    # This would typically involve creating a position with orders from a previous day
    # For now, we'll test it assuming the YOLO strategy's implementation doesn't require this detail
    context = PDTContext(
        position=long_dummy_position, order=sell_order, count_of_positions_opened_today=0, rolling_day_trade_count=3
    )
    decision = strategy.evaluate_order(context)
    assert decision.allowed is True

    # Test case: sell of position opened today with day trades available
    context = PDTContext(
        position=long_dummy_position,
        order=sell_order,
        count_of_positions_opened_today=1,  # Position opened today
        rolling_day_trade_count=0,  # Day trades available
    )
    decision = strategy.evaluate_order(context)
    assert decision.allowed is True

    # Test case: sell of position opened today with no day trades available
    # This would depend on the YOLO strategy's implementation for checking day trades
    context = PDTContext(
        position=long_dummy_position,
        order=sell_order,
        count_of_positions_opened_today=1,  # Position opened today
        rolling_day_trade_count=3,  # No day trades available
    )
    decision = strategy.evaluate_order(context)
    # Check if YOLO strategy allows or disallows this based on implementation
    # The original test expected this to be False
    assert decision.allowed is False
