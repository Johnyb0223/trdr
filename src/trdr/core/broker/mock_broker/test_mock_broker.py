import pytest
import asyncio
from decimal import Decimal

from .mock_broker import MockBroker
from ..models import OrderSide, PositionSide, Money


def test_that_constructor_raises_error():
    with pytest.raises(TypeError, match="Use MockBroker.create()"):
        MockBroker()


def test_create_returns_initialized_broker():
    broker = asyncio.run(MockBroker.create())

    assert broker is not None
    assert isinstance(broker, MockBroker)


def test_refresh_sets_default_values(mock_broker, dummy_position):
    # Force refresh by clearing state and manually calling refresh
    mock_broker._clear_current_state()
    asyncio.run(mock_broker._refresh())

    # Verify default values were set
    assert mock_broker._cash == Money(amount=Decimal(10000))
    assert mock_broker._equity == Money(amount=Decimal(15000))
    assert mock_broker._day_trade_count == 0
    assert len(mock_broker._positions) == 3
    assert "AAPL" in mock_broker._positions
    assert "MSFT" in mock_broker._positions
    assert "GOOG" in mock_broker._positions

    # Verify position properties
    position = mock_broker._positions["AAPL"]
    assert position.symbol == dummy_position.symbol
    assert position.quantity == dummy_position.quantity
    assert position.average_cost == dummy_position.average_cost
    assert position.side == dummy_position.side


def test_get_positions_returns_mock_positions(mock_broker, dummy_position):
    positions = asyncio.run(mock_broker.get_positions())

    assert positions is not None
    assert len(positions) == 3
    assert "AAPL" in positions
    assert "MSFT" in positions
    assert "GOOG" in positions

    position = positions["AAPL"]
    assert position.symbol == dummy_position.symbol
    assert position.quantity == dummy_position.quantity
    assert position.average_cost == dummy_position.average_cost
    assert position.side == dummy_position.side


def test_get_position_returns_position_for_existing_symbol(mock_broker, dummy_position):
    position = asyncio.run(mock_broker.get_position("AAPL"))

    assert position is not None
    assert position.symbol == dummy_position.symbol
    assert position.quantity == dummy_position.quantity
    assert position.average_cost == dummy_position.average_cost
    assert position.side == dummy_position.side


def test_get_position_returns_none_for_nonexistent_symbol(mock_broker):
    position = asyncio.run(mock_broker.get_position("NONEXISTENT"))
    assert position is None


def test_get_available_cash_returns_mock_cash(mock_broker):
    cash = asyncio.run(mock_broker.get_available_cash())
    assert cash == Money(amount=Decimal(10000))


def test_get_equity_returns_mock_equity(mock_broker):
    equity = asyncio.run(mock_broker.get_equity())
    assert equity == Money(amount=Decimal(15000))


def test_get_account_exposure_calculates_correctly(mock_broker):
    # Mock broker has three positions:
    # - AAPL: 10 shares at $100 = $1000
    # - MSFT: 5 shares at $200 = $1000
    # - GOOG: 2 shares at $500 = $1000
    # Total position value = $3000
    # Equity = 15000
    # Expected exposure = 3000 / 15000 = 0.2
    exposure = asyncio.run(mock_broker.get_account_exposure())
    assert exposure == Decimal("0.2")
    assert float(exposure) == pytest.approx(0.2, abs=0.001)


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
            assert cash == Money(amount=Decimal(10000))
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
    assert mock_broker._cash == Money(amount=Decimal(10000))
    assert mock_broker._is_stale_flag is False
