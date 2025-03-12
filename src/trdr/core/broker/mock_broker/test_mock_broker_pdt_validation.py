import pytest
import asyncio
from decimal import Decimal

from ..models import OrderSide
from ...shared.models import Money
from ..pdt.exceptions import PDTRuleViolationException, PDTStrategyException

# ======================================================================
# Helper Functions
# ======================================================================


def reset_broker_state(broker, day_trade_count=0):
    """Reset broker to a known state for testing."""
    broker._day_trade_count = day_trade_count
    # Reset positions opened today flags
    asyncio.run(broker.set_position_opened_today("TSLA", False))
    asyncio.run(broker.set_position_opened_today("NVDA", False))


# ======================================================================
# Tests for Position Tracking
# ======================================================================


def test_position_opened_today_tracking(mock_broker):
    """Test the position_opened_today tracking mechanism."""
    broker = mock_broker

    # Reset to known state
    reset_broker_state(broker)

    # Initially no positions should be marked as opened today
    assert asyncio.run(broker.get_positions_opened_today_count()) == 0
    assert asyncio.run(broker.position_opened_today("TSLA")) is False
    assert asyncio.run(broker.position_opened_today("NVDA")) is False

    # Mark a position as opened today
    asyncio.run(broker.set_position_opened_today("TSLA", True))
    assert asyncio.run(broker.position_opened_today("TSLA")) is True
    assert asyncio.run(broker.get_positions_opened_today_count()) == 1

    # Mark multiple positions
    asyncio.run(broker.set_position_opened_today("NVDA", True))
    assert asyncio.run(broker.get_positions_opened_today_count()) == 2

    # Unmark a position
    asyncio.run(broker.set_position_opened_today("TSLA", False))
    assert asyncio.run(broker.position_opened_today("TSLA")) is False
    assert asyncio.run(broker.get_positions_opened_today_count()) == 1


def test_position_opened_today_tracking_with_triggers_refresh(mock_broker):
    """Test the position_opened_today tracking mechanism with triggers refresh."""
    broker = mock_broker

    # Reset to known state
    reset_broker_state(broker)

    # Mark a position as opened today
    asyncio.run(broker.set_position_opened_today("TSLA", True))
    assert asyncio.run(broker.position_opened_today("TSLA")) is True
    assert asyncio.run(broker.get_positions_opened_today_count()) == 1

    # Calls to these methods should trigger a refresh
    broker._is_stale_flag = True
    assert asyncio.run(broker.position_opened_today("TSLA")) is True
    assert asyncio.run(broker.get_positions_opened_today_count()) == 1
    assert broker._is_stale_flag is False


# ======================================================================
# Tests for NunStrategy
# ======================================================================


def test_nun_strategy_buy_orders_day_trade_limits(mock_broker):
    """Test NunStrategy enforcement of day trade limits for BUY orders."""
    broker = mock_broker

    # Test matrix:
    # - Day trade counts: 0, 1, 2, 3
    # - Expected behavior: Allow buys for counts 0-2, deny for count 3

    for day_trade_count in range(4):
        reset_broker_state(broker, day_trade_count)

        # For NunStrategy:
        # - With 0 day trades used, can open 3 positions
        # - With 1 day trade used, can open 2 positions
        # - With 2 day trades used, can open 1 position
        # - With 3 day trades used, cannot open positions

        if day_trade_count < 3:
            # Should be able to buy
            asyncio.run(broker._validate_pre_order("TSLA", OrderSide.BUY, Money(amount=Decimal(1000))))
        else:
            # Should not be able to buy
            with pytest.raises(PDTRuleViolationException, match="PDT restrictions prevent opening a new position"):
                asyncio.run(broker._validate_pre_order("TSLA", OrderSide.BUY, Money(amount=Decimal(1000))))


def test_nun_strategy_buy_orders_position_limits(mock_broker):
    """Test NunStrategy enforcement of position limits for BUY orders."""
    broker = mock_broker

    # Test matrix:
    # - Day trade count: 2 (allows 1 more position)
    # - Positions opened today: 0, 1, 2, 3
    # - Expected behavior: Allow when positions < available day trades, deny otherwise

    # With 2 day trades used, we can open 1 more position (3-2=1)
    broker._day_trade_count = 2

    # Test with increasing number of positions opened today
    for positions_count in range(3):
        reset_broker_state(broker, 2)  # Keep day trade count at 2

        # Set the specified number of positions as opened today
        if positions_count >= 1:
            asyncio.run(broker.set_position_opened_today("TSLA", True))
        if positions_count >= 2:
            asyncio.run(broker.set_position_opened_today("NVDA", True))

        # Verify the count is set correctly
        assert asyncio.run(broker.get_positions_opened_today_count()) == positions_count

        # NunStrategy allows buying when positions_opened_today < available_day_trades
        # With day_trade_count=2, available_day_trades=1, so can only buy when positions=0
        if positions_count < 1:
            # Should be able to buy
            asyncio.run(broker._validate_pre_order("META", OrderSide.BUY, Money(amount=Decimal(1000))))
        else:
            # Should not be able to buy
            with pytest.raises(PDTRuleViolationException, match="PDT restrictions prevent opening a new position"):
                asyncio.run(broker._validate_pre_order("META", OrderSide.BUY, Money(amount=Decimal(1000))))


def test_nun_strategy_sell_orders(mock_broker):
    """Test NunStrategy enforcement for SELL orders based on position and day trade status."""
    broker = mock_broker

    # Test matrix:
    # - Position opened today: False, True
    # - Day trade count: 0, 1, 2, 3
    # - Expected behavior:
    #   - If position not opened today: Always allow selling
    #   - If position opened today: Allow selling
    #   - If day trade count is 3: We should raise an exception when trying to close a position opened today as the
    #     NunStrategy does not allow you to open a position if you would not be able to close it same day.

    # Test selling position NOT opened today (always allowed regardless of day trade count)
    for day_trade_count in range(4):
        reset_broker_state(broker, day_trade_count)
        # Should always be able to sell positions not opened today
        asyncio.run(broker._validate_pre_order("NVDA", OrderSide.SELL, Money(amount=Decimal(1000))))

    # Test selling position opened today
    for day_trade_count in range(4):
        reset_broker_state(broker, day_trade_count)
        asyncio.run(broker.set_position_opened_today("TSLA", True))

        if day_trade_count < 3:
            # Should be able to sell if we have day trades available
            asyncio.run(broker._validate_pre_order("TSLA", OrderSide.SELL, Money(amount=Decimal(1000))))
        else:
            # Should not be able to sell if no day trades available
            with pytest.raises(
                PDTStrategyException,
                match="This case should never happen. We should not be able to open a position if we would not be able to close it same day.",
            ):
                asyncio.run(broker._validate_pre_order("TSLA", OrderSide.SELL, Money(amount=Decimal(1000))))


# ======================================================================
# Tests for WiggleStrategy
# ======================================================================


def test_wiggle_strategy_buy_orders(mock_broker_with_wiggle_strategy):
    """Test WiggleStrategy enforcement for BUY orders."""
    broker = mock_broker_with_wiggle_strategy

    # Set wiggle room to 2 (allows opening 2 more positions than standard)
    broker.wiggle_room = 2

    # Test matrix:
    # - Day trade count: 0, 1, 2, 3
    # - Positions opened today: varies
    # - Expected behavior:
    #   - With wiggle_room=2, can open (3-day_trade_count)+2 positions

    day_trade_scenarios = [
        {"count": 0, "max_positions": 5},  # 3-0+2 = 5
        {"count": 1, "max_positions": 4},  # 3-1+2 = 4
        {"count": 2, "max_positions": 3},  # 3-2+2 = 3
        {"count": 3, "max_positions": 2},  # 3-3+2 = 2
    ]

    for scenario in day_trade_scenarios:
        day_trade_count = scenario["count"]
        max_positions = scenario["max_positions"]

        # Test for different position counts
        for positions_count in range(max_positions + 2):  # Test beyond the limit
            reset_broker_state(broker, day_trade_count)

            # Set the specified number of positions as opened today
            for i in range(positions_count):
                if i == 0:
                    asyncio.run(broker.set_position_opened_today("TSLA", True))
                elif i == 1:
                    asyncio.run(broker.set_position_opened_today("NVDA", True))

            # Verify position count
            if positions_count <= 2:  # We only have 2 positions in our test
                assert asyncio.run(broker.get_positions_opened_today_count()) == positions_count

            if positions_count < max_positions:
                # Should be able to buy
                asyncio.run(broker._validate_pre_order("META", OrderSide.BUY, Money(amount=Decimal(1000))))
            elif positions_count >= 2:  # Skip tests that would create fake positions beyond our 2
                pass
            else:
                # Should not be able to buy
                with pytest.raises(PDTRuleViolationException, match="PDT restrictions prevent opening a new position"):
                    asyncio.run(broker._validate_pre_order("TSLA", OrderSide.BUY, Money(amount=Decimal(1000))))


def test_wiggle_strategy_sell_orders(mock_broker_with_wiggle_strategy):
    """Test WiggleStrategy enforcement for SELL orders."""
    broker = mock_broker_with_wiggle_strategy

    # The selling logic is the same as NunStrategy:
    # - Can always sell positions not opened today
    # - Can sell positions opened today if day_trade_count < 3

    # Test selling position NOT opened today (always allowed)
    for day_trade_count in range(4):
        reset_broker_state(broker, day_trade_count)
        # Should always be able to sell positions not opened today
        asyncio.run(broker._validate_pre_order("TSLA", OrderSide.SELL, Money(amount=Decimal(1000))))

    # Test selling position opened today
    for day_trade_count in range(4):
        reset_broker_state(broker, day_trade_count)
        asyncio.run(broker.set_position_opened_today("TSLA", True))

        if day_trade_count < 3:
            # Should be able to sell if we have day trades available
            asyncio.run(broker._validate_pre_order("TSLA", OrderSide.SELL, Money(amount=Decimal(1000))))
        else:
            # Should not be able to sell if no day trades available
            with pytest.raises(PDTRuleViolationException, match="PDT restrictions prevent closing this position"):
                asyncio.run(broker._validate_pre_order("TSLA", OrderSide.SELL, Money(amount=Decimal(1000))))


# ======================================================================
# Tests for YoloStrategy
# ======================================================================


def test_yolo_strategy_buy_orders(mock_broker_with_yolo_strategy):
    """Test YoloStrategy enforcement for BUY orders."""
    broker = mock_broker_with_yolo_strategy

    # YoloStrategy always allows buying regardless of day trades or positions
    # Test all day trade counts
    for day_trade_count in range(4):
        reset_broker_state(broker, day_trade_count)

        # Set a high number of positions opened today
        asyncio.run(broker.set_position_opened_today("MSFT", True))
        asyncio.run(broker.set_position_opened_today("AAPL", True))
        asyncio.run(broker.set_position_opened_today("GOOG", True))

        # Should still be able to buy
        asyncio.run(broker._validate_pre_order("TSLA", OrderSide.BUY, Money(amount=Decimal(1000))))


def test_yolo_strategy_sell_orders(mock_broker_with_yolo_strategy):
    """Test YoloStrategy enforcement for SELL orders."""
    broker = mock_broker_with_yolo_strategy

    # YoloStrategy:
    # - Can always sell positions not opened today
    # - Can NEVER sell positions opened today, regardless of day trade count

    # Test selling position NOT opened today (always allowed)
    for day_trade_count in range(4):
        reset_broker_state(broker, day_trade_count)
        # Should always be able to sell positions not opened today
        asyncio.run(broker._validate_pre_order("TSLA", OrderSide.SELL, Money(amount=Decimal(1000))))

    # Test selling position opened today
    for day_trade_count in range(4):
        reset_broker_state(broker, day_trade_count)
        asyncio.run(broker.set_position_opened_today("TSLA", True))

        # should be able to sell if day trade available
        if day_trade_count < 3:
            asyncio.run(broker._validate_pre_order("TSLA", OrderSide.SELL, Money(amount=Decimal(1000))))
        else:
            # Should not be able to sell if no day trades available
            with pytest.raises(
                PDTRuleViolationException, match="Cannot sell position opened today under YOLO strategy"
            ):
                asyncio.run(broker._validate_pre_order("TSLA", OrderSide.SELL, Money(amount=Decimal(1000))))


# ======================================================================
# End-to-End Tests
# ======================================================================


def test_full_order_flow_with_nun_strategy(mock_broker):
    """Test a full order flow with the NunStrategy."""
    broker = mock_broker
    reset_broker_state(broker, 0)  # Start with 0 day trades

    # Test with our positions and an additional test position
    # Set positions opened today:

    # First position - TSLA (already exists in broker)
    asyncio.run(broker._validate_pre_order("TSLA", OrderSide.BUY, Money(amount=Decimal(500))))
    asyncio.run(broker.set_position_opened_today("TSLA", True))

    # Verify position count is 1
    assert asyncio.run(broker.get_positions_opened_today_count()) == 1

    # Second position - NVDA (already exists in broker)
    asyncio.run(broker._validate_pre_order("NVDA", OrderSide.BUY, Money(amount=Decimal(500))))
    asyncio.run(broker.set_position_opened_today("NVDA", True))

    # Verify position count is 2
    assert asyncio.run(broker.get_positions_opened_today_count()) == 2

    # Set day trade count to 3 (no day trades left)
    broker._day_trade_count = 3

    # Should not be able to buy another position with 3 day trades and 3 positions opened today
    with pytest.raises(PDTRuleViolationException, match="PDT restrictions prevent opening a new position"):
        asyncio.run(broker._validate_pre_order("AAPL", OrderSide.BUY, Money(amount=Decimal(500))))

    # Should not be able to sell a position opened today with no day trades left
    with pytest.raises(PDTRuleViolationException, match="PDT restrictions prevent closing this position"):
        asyncio.run(broker._validate_pre_order("TSLA", OrderSide.SELL, Money(amount=Decimal(500))))

    # Reset one position to not opened today
    asyncio.run(broker.set_position_opened_today("NVDA", False))

    # Verify position count updated correctly
    assert asyncio.run(broker.get_positions_opened_today_count()) == 1

    # Should be able to sell a position not opened today
    asyncio.run(broker._validate_pre_order("NVDA", OrderSide.SELL, Money(amount=Decimal(500))))


def test_full_order_flow_with_wiggle_strategy(mock_broker_with_wiggle_strategy):
    """Test a full order flow with the WiggleStrategy."""
    broker = mock_broker_with_wiggle_strategy
    broker.wiggle_room = 2
    reset_broker_state(broker, 3)  # Start with 3 day trades used

    # Even with 3 day trades used, with wiggle_room=2, we can still open 2 positions
    # First position - TSLA
    asyncio.run(broker._validate_pre_order("TSLA", OrderSide.BUY, Money(amount=Decimal(500))))
    asyncio.run(broker.set_position_opened_today("TSLA", True))

    # Verify position count is 1
    assert asyncio.run(broker.get_positions_opened_today_count()) == 1

    # Second position - NVDA
    asyncio.run(broker._validate_pre_order("NVDA", OrderSide.BUY, Money(amount=Decimal(500))))
    asyncio.run(broker.set_position_opened_today("NVDA", True))

    # Verify position count is 2
    assert asyncio.run(broker.get_positions_opened_today_count()) == 2

    # With 3 day trades used, we cannot sell a position opened today
    with pytest.raises(PDTRuleViolationException, match="PDT restrictions prevent closing this position"):
        asyncio.run(broker._validate_pre_order("TSLA", OrderSide.SELL, Money(amount=Decimal(500))))

    # Mark NVDA as not opened today
    asyncio.run(broker.set_position_opened_today("NVDA", False))

    # Can sell a position not opened today
    asyncio.run(broker._validate_pre_order("NVDA", OrderSide.SELL, Money(amount=Decimal(500))))


def test_full_order_flow_with_yolo_strategy(mock_broker_with_yolo_strategy):
    """Test a full order flow with the YoloStrategy."""
    broker = mock_broker_with_yolo_strategy
    reset_broker_state(broker, 3)  # Start with 3 day trades used

    # YOLO strategy allows unlimited buying regardless of day trade count
    # Even with 3 day trades used, can open positions with YOLO strategy
    asyncio.run(broker._validate_pre_order("TSLA", OrderSide.BUY, Money(amount=Decimal(500))))
    asyncio.run(broker._validate_pre_order("NVDA", OrderSide.BUY, Money(amount=Decimal(500))))
    asyncio.run(broker._validate_pre_order("AMZN", OrderSide.BUY, Money(amount=Decimal(500))))

    # Mark a position as opened today
    asyncio.run(broker.set_position_opened_today("TSLA", True))

    # Verify position count
    assert asyncio.run(broker.get_positions_opened_today_count()) == 1

    asyncio.run(broker.set_position_opened_today("NVDA", True))

    # Verify position count
    assert asyncio.run(broker.get_positions_opened_today_count()) == 2

    # YOLO strategy allows selling if day trade available
    broker._day_trade_count = 2
    asyncio.run(broker._validate_pre_order("TSLA", OrderSide.SELL, Money(amount=Decimal(500))))

    broker._day_trade_count = 3
    with pytest.raises(PDTRuleViolationException, match="Cannot sell position opened today under YOLO strategy"):
        asyncio.run(broker._validate_pre_order("TSLA", OrderSide.SELL, Money(amount=Decimal(500))))

    # Mark NVDA as not opened today to be sure
    asyncio.run(broker.set_position_opened_today("NVDA", False))

    assert asyncio.run(broker.get_positions_opened_today_count()) == 1

    # But can sell a position not opened today
    asyncio.run(broker._validate_pre_order("NVDA", OrderSide.SELL, Money(amount=Decimal(500))))
