import pytest
import asyncio
from decimal import Decimal

from .mock_broker import MockBroker
from ..models import OrderSide, Money


def test_that_constructor_raises_error():
    with pytest.raises(TypeError, match="Use MockBroker.create()"):
        MockBroker()


def test_create_returns_initialized_broker():
    broker = asyncio.run(MockBroker.create())

    assert broker is not None
    assert isinstance(broker, MockBroker)


def test_refresh_sets_default_values(mock_broker):
    # Force refresh by clearing state and manually calling refresh
    mock_broker._clear_current_state()
    asyncio.run(mock_broker._refresh())

    # Verify default values were set
    assert mock_broker._cash == Money(amount=Decimal(100000))
    assert mock_broker._day_trade_count == 1
    assert len(mock_broker._positions) == 2
    assert "TSLA" in mock_broker._positions
    assert "NVDA" in mock_broker._positions

    # Calculate expected equity (cash + position values)
    tsla_value = mock_broker._positions["TSLA"].quantity * mock_broker._positions["TSLA"].average_cost.amount
    nvda_value = mock_broker._positions["NVDA"].quantity * mock_broker._positions["NVDA"].average_cost.amount
    expected_equity = Decimal(100000) + tsla_value + nvda_value
    assert mock_broker._equity.amount == expected_equity

    # Verify position properties
    position_tsla = mock_broker._positions["TSLA"]
    assert position_tsla.symbol == "TSLA"
    assert position_tsla.quantity == Decimal(10)
    assert position_tsla.average_cost.amount == Decimal(250)
    assert position_tsla.side == PositionSide.LONG

    position_nvda = mock_broker._positions["NVDA"]
    assert position_nvda.symbol == "NVDA"
    assert position_nvda.quantity == Decimal(20)
    assert position_nvda.average_cost.amount == Decimal(125)
    assert position_nvda.side == PositionSide.LONG


def test_get_positions_returns_mock_positions(mock_broker):
    positions = asyncio.run(mock_broker.get_positions())

    assert positions is not None
    assert len(positions) == 2
    assert "TSLA" in positions
    assert "NVDA" in positions

    position_tsla = positions["TSLA"]
    assert position_tsla.symbol == "TSLA"
    assert position_tsla.quantity == Decimal(10)
    assert position_tsla.average_cost.amount == Decimal(250)
    assert position_tsla.side == PositionSide.LONG

    position_nvda = positions["NVDA"]
    assert position_nvda.symbol == "NVDA"
    assert position_nvda.quantity == Decimal(20)
    assert position_nvda.average_cost.amount == Decimal(125)
    assert position_nvda.side == PositionSide.LONG


def test_get_position_returns_position_for_existing_symbol(mock_broker):
    position = asyncio.run(mock_broker.get_position("TSLA"))

    assert position is not None
    assert position.symbol == "TSLA"
    assert position.quantity == Decimal(10)
    assert position.average_cost.amount == Decimal(250)
    assert position.side == PositionSide.LONG


def test_get_position_returns_none_for_nonexistent_symbol(mock_broker):
    position = asyncio.run(mock_broker.get_position("NONEXISTENT"))
    assert position is None


def test_get_available_cash_returns_mock_cash(mock_broker):
    cash = asyncio.run(mock_broker.get_available_cash())
    assert cash == Money(amount=Decimal(100000))


def test_get_equity_returns_calculated_equity(mock_broker):
    # Get cash and positions to calculate expected equity
    cash = asyncio.run(mock_broker.get_available_cash())
    positions = asyncio.run(mock_broker.get_positions())

    # Calculate expected equity (cash + position values)
    position_value = sum(pos.quantity * pos.average_cost.amount for pos in positions.values())
    expected_equity = cash.amount + position_value

    equity = asyncio.run(mock_broker.get_equity())
    assert equity.amount == expected_equity


def test_get_account_exposure_calculates_correctly(mock_broker):
    # Mock broker has two positions:
    # - TSLA: 10 shares at $250 = $2,500
    # - NVDA: 20 shares at $125 = $2,500
    # Total position value = $5,000
    # Cash = $100,000
    # Equity = $105,000
    # Expected exposure = 5000 / 105000 ≈ 0.048
    exposure = asyncio.run(mock_broker.get_account_exposure())

    # Calculate expected exposure manually
    positions = asyncio.run(mock_broker.get_positions())
    equity = asyncio.run(mock_broker.get_equity())
    position_value = sum(pos.quantity * pos.average_cost.amount for pos in positions.values())
    expected_exposure = position_value / equity.amount

    assert exposure == expected_exposure
    assert float(exposure) == pytest.approx(0.048, abs=0.001)


def test_get_position_exposure_returns_zero_for_nonexistent_symbol(mock_broker):
    exposure = asyncio.run(mock_broker.get_position_exposure("NONEXISTENT"))
    assert exposure == 0


def test_place_order_completes_without_error(mock_broker):
    # Just verify no exceptions are raised
    asyncio.run(mock_broker.place_order("MSFT", OrderSide.BUY, Money(amount=Decimal(500))))
    # Verify state is marked as stale
    assert mock_broker._is_stale_flag is True


def test_cancel_all_orders_completes_without_error(mock_broker):
    # Just verify no exceptions are raised
    asyncio.run(mock_broker.cancel_all_orders())
    # In base_broker.py, the stale flag is set to True before calling _cancel_all_orders
    # but then reset to False after the stale_handler is called
    assert mock_broker._is_stale_flag is True


def test_position_opened_today_returns_false(mock_broker):
    result = asyncio.run(mock_broker._position_opened_today("AAPL"))
    assert result is False


def test_broker_as_context_manager():
    async def run_context_manager_test():
        # Don't need to explicitly create NunStrategy since it's the default
        async with await MockBroker.create() as broker:
            cash = await broker.get_available_cash()
            assert cash == Money(amount=Decimal(100000))
        # After exiting context, session should be closed
        assert broker._session is None

    asyncio.run(run_context_manager_test())


def test_stale_handler_refreshes_when_stale(mock_broker):
    # Force state to be stale but maintain updated_dt to avoid NoneType error
    mock_broker._is_stale_flag = True
    original_updated_dt = mock_broker._updated_dt

    # Clear cash to verify refresh happens
    mock_broker._cash = None
    assert mock_broker._cash is None

    # Restore updated_dt to avoid timestamp error
    mock_broker._updated_dt = original_updated_dt

    # Call stale handler
    asyncio.run(mock_broker._stale_handler())

    # Verify state was refreshed
    assert mock_broker._cash == Money(amount=Decimal(100000))
    assert mock_broker._is_stale_flag is False

    # Verify positions were initialized correctly
    assert len(mock_broker._positions) == 2
    assert "TSLA" in mock_broker._positions
    assert "NVDA" in mock_broker._positions


# ======================================================================
# Tests for Order Placement and Position Updates
# ======================================================================


def test_buy_order_adds_pending_order(mock_broker):
    """Test that placing a buy order adds it to the pending orders list."""
    # Place an order
    order_symbol = "AAPL"
    order_amount = Decimal(5000)
    asyncio.run(mock_broker.place_order(order_symbol, OrderSide.BUY, Money(amount=order_amount)))

    # Verify pending order
    pending_orders = asyncio.run(mock_broker.get_pending_orders())
    assert len(pending_orders) == 1
    assert pending_orders[0]["symbol"] == order_symbol
    assert pending_orders[0]["side"] == OrderSide.BUY
    assert pending_orders[0]["dollar_amount"].amount == order_amount

    # Verify stale flag is set
    assert mock_broker._is_stale_flag is True


def test_sell_order_adds_pending_order(mock_broker):
    """Test that placing a sell order adds it to the pending orders list."""
    # Place an order for an existing position
    asyncio.run(mock_broker.place_order("TSLA", OrderSide.SELL, Money(amount=Decimal(2500))))

    # Verify pending order
    pending_orders = asyncio.run(mock_broker.get_pending_orders())
    assert len(pending_orders) == 1
    assert pending_orders[0]["symbol"] == "TSLA"
    assert pending_orders[0]["side"] == OrderSide.SELL
    assert pending_orders[0]["dollar_amount"].amount == Decimal(2500)

    # Verify stale flag is set
    assert mock_broker._is_stale_flag is True


def test_stale_handler_processes_buy_order(mock_broker):
    """Test that the stale handler processes a buy order and updates positions."""
    # Get initial cash and equity
    initial_cash = asyncio.run(mock_broker.get_available_cash()).amount
    initial_equity = asyncio.run(mock_broker.get_equity()).amount

    # Place a buy order
    new_symbol = "AAPL"
    order_amount = Decimal(5000)
    asyncio.run(mock_broker.place_order(new_symbol, OrderSide.BUY, Money(amount=order_amount)))

    # Trigger stale handler by getting positions
    positions = asyncio.run(mock_broker.get_positions())

    # Verify new position was added
    assert new_symbol in positions
    new_position = positions[new_symbol]
    assert new_position.symbol == new_symbol
    assert new_position.quantity == Decimal(50)  # $5000 / $100 per share
    assert new_position.average_cost.amount == Decimal(100)
    assert new_position.side == PositionSide.LONG

    # Verify cash was reduced
    new_cash = asyncio.run(mock_broker.get_available_cash()).amount
    assert new_cash == initial_cash - order_amount

    # Verify equity remains the same (cash goes down, position value goes up)
    new_equity = asyncio.run(mock_broker.get_equity()).amount
    assert new_equity == initial_equity

    # Verify pending orders were cleared
    pending_orders = asyncio.run(mock_broker.get_pending_orders())
    assert len(pending_orders) == 0

    # Verify position was marked as opened today
    assert asyncio.run(mock_broker._position_opened_today(new_symbol)) is True


def test_stale_handler_processes_sell_order(mock_broker):
    """Test that the stale handler processes a sell order and removes positions."""
    # Get initial cash and equity
    initial_cash = asyncio.run(mock_broker.get_available_cash()).amount
    initial_equity = asyncio.run(mock_broker.get_equity()).amount

    # Get initial position value
    positions = asyncio.run(mock_broker.get_positions())
    position_symbol = "TSLA"
    position = positions[position_symbol]
    position_value = position.quantity * position.average_cost.amount

    # Place a sell order
    asyncio.run(
        mock_broker.place_order(
            position_symbol,
            OrderSide.SELL,
            Money(amount=Decimal(2500)),  # Amount doesn't matter for complete liquidation
        )
    )

    # Trigger stale handler by getting positions
    positions = asyncio.run(mock_broker.get_positions())

    # Verify position was removed
    assert position_symbol not in positions

    # Verify cash was increased by position value
    new_cash = asyncio.run(mock_broker.get_available_cash()).amount
    assert new_cash == initial_cash + position_value

    # Verify equity remains the same (cash goes up, position value goes down)
    new_equity = asyncio.run(mock_broker.get_equity()).amount
    assert new_equity == initial_equity

    # Verify pending orders were cleared
    pending_orders = asyncio.run(mock_broker.get_pending_orders())
    assert len(pending_orders) == 0


def test_multiple_orders_sequence(mock_broker):
    """Test a sequence of buy and sell orders and verify broker state."""
    # Get initial state
    initial_cash = asyncio.run(mock_broker.get_available_cash()).amount
    initial_positions = asyncio.run(mock_broker.get_positions()).copy()
    assert len(initial_positions) == 2

    # Step 1: Buy new position
    buy_symbol = "AAPL"
    buy_amount = Decimal(10000)
    asyncio.run(mock_broker.place_order(buy_symbol, OrderSide.BUY, Money(amount=buy_amount)))

    # Trigger stale handler
    positions = asyncio.run(mock_broker.get_positions())

    # Verify new position was added
    assert buy_symbol in positions
    assert len(positions) == 3

    # Verify cash decreased
    cash_after_buy = asyncio.run(mock_broker.get_available_cash()).amount
    assert cash_after_buy == initial_cash - buy_amount

    # Step 2: Sell existing position
    sell_symbol = "NVDA"
    asyncio.run(
        mock_broker.place_order(
            sell_symbol, OrderSide.SELL, Money(amount=Decimal(1000))  # Amount doesn't matter for complete liquidation
        )
    )

    # Trigger stale handler
    positions = asyncio.run(mock_broker.get_positions())

    # Verify position was removed
    assert sell_symbol not in positions
    assert len(positions) == 2

    # Verify cash increased
    cash_after_sell = asyncio.run(mock_broker.get_available_cash()).amount
    expected_cash_change = initial_positions[sell_symbol].quantity * initial_positions[sell_symbol].average_cost.amount
    assert cash_after_sell == cash_after_buy + expected_cash_change

    # Step 3: Buy more of existing position
    buy_more_symbol = "TSLA"
    buy_more_amount = Decimal(5000)
    original_quantity = positions[buy_more_symbol].quantity

    asyncio.run(mock_broker.place_order(buy_more_symbol, OrderSide.BUY, Money(amount=buy_more_amount)))

    # Trigger stale handler
    positions = asyncio.run(mock_broker.get_positions())

    # Verify position was updated
    assert buy_more_symbol in positions
    updated_position = positions[buy_more_symbol]
    additional_quantity = Decimal(buy_more_amount / 100)  # $5000 / $100 per share
    assert updated_position.quantity == original_quantity + additional_quantity

    # Verify cash decreased
    final_cash = asyncio.run(mock_broker.get_available_cash()).amount
    assert final_cash == cash_after_sell - buy_more_amount


def test_cancel_all_orders_clears_pending_orders(mock_broker):
    """Test that cancel_all_orders clears the pending orders list."""
    # Place multiple orders
    asyncio.run(mock_broker.place_order("AAPL", OrderSide.BUY, Money(amount=Decimal(5000))))
    asyncio.run(mock_broker.place_order("MSFT", OrderSide.BUY, Money(amount=Decimal(7500))))

    # Verify pending orders
    pending_orders = asyncio.run(mock_broker.get_pending_orders())
    assert len(pending_orders) == 2

    # Cancel all orders
    asyncio.run(mock_broker.cancel_all_orders())

    # Verify pending orders are cleared
    pending_orders = asyncio.run(mock_broker.get_pending_orders())
    assert len(pending_orders) == 0

    # Verify stale flag is set
    assert mock_broker._is_stale_flag is True

    # Trigger stale handler and verify no positions were added
    initial_positions = asyncio.run(mock_broker.get_positions())
    initial_count = len(initial_positions)

    # Force refresh
    asyncio.run(mock_broker._stale_handler())

    # Check positions again
    final_positions = asyncio.run(mock_broker.get_positions())
    assert len(final_positions) == initial_count  # No change in position count
