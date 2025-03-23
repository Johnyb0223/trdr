import pytest
import asyncio
from decimal import Decimal
from unittest.mock import AsyncMock, patch, MagicMock

from .trading_context import TradingContext
from .exceptions import MissingContextValue
from ..shared.models import ContextIdentifier, Timeframe, Money
from ..security_provider.models import Security


def test_trading_context_direct_initialization_raises_type_error(
    security_provider_with_fake_data, mock_broker_with_nun_strategy
):
    """Test that direct initialization throws TypeError."""
    with pytest.raises(TypeError):
        TradingContext(security_provider_with_fake_data, mock_broker_with_nun_strategy)


def test_trading_context_creation_with_factory_method(mock_trading_context: TradingContext):
    """Test factory method creation initializes properties correctly."""
    assert mock_trading_context is not None
    assert mock_trading_context.symbol_stack is not None
    assert mock_trading_context.current_symbol is None
    assert mock_trading_context.current_position is None
    assert mock_trading_context.current_security is None

    set_of_symbols = set(mock_trading_context.symbol_stack)
    assert set_of_symbols == set(mock_trading_context.security_provider._bar_provider._data_cache.keys())
    assert set_of_symbols == set(mock_trading_context.security_provider._bar_provider.get_symbols())


def test_trading_context_next_symbol(mock_trading_context: TradingContext):
    """Test advancing to next symbol successfully updates context properties."""
    assert mock_trading_context.current_symbol is None
    assert mock_trading_context.current_position is None
    assert mock_trading_context.current_security is None

    # First call to next_symbol
    result = asyncio.run(mock_trading_context.next_symbol())
    assert result is True

    list_of_symbols = asyncio.run(mock_trading_context.security_provider.get_symbols())
    assert mock_trading_context.current_symbol == list_of_symbols[0]
    # Position may be None if no position exists for this symbol
    assert mock_trading_context.current_security is not None
    assert mock_trading_context.current_security.symbol == mock_trading_context.current_symbol


def test_trading_context_process_all_symbols(mock_trading_context: TradingContext):
    """Test processing all symbols and then returning false when complete."""
    # Get total number of symbols
    total_symbols = len(mock_trading_context.symbol_stack)

    # Process all symbols
    for i in range(total_symbols):
        result = asyncio.run(mock_trading_context.next_symbol())
        assert result is True
        assert mock_trading_context.current_symbol is not None
        assert mock_trading_context.current_security is not None

    # Try one more time - should return False and reset values
    result = asyncio.run(mock_trading_context.next_symbol())
    assert result is False
    assert mock_trading_context.current_symbol is None
    assert mock_trading_context.current_position is None
    assert mock_trading_context.current_security is None


def test_trading_context_empty_symbol_list():
    """Test behavior with empty symbol list."""
    # Create mocks for dependencies
    mock_security_provider = AsyncMock()
    mock_broker = AsyncMock()

    # Configure the security provider to return empty list
    mock_security_provider.get_symbols.return_value = []

    # Create context with empty symbol list
    context = asyncio.run(TradingContext.create(mock_security_provider, mock_broker))

    # Verify symbol stack is empty
    assert context.symbol_stack == []

    # Try to get next symbol
    result = asyncio.run(context.next_symbol())

    # Verify returns False and context values are None
    assert result is False
    assert context.current_symbol is None
    assert context.current_position is None
    assert context.current_security is None


def test_next_symbol_security_symbol_mismatch(mock_trading_context: TradingContext):
    """Test error when security's symbol doesn't match current symbol."""
    # Create a mock for get_security that returns a mismatched symbol
    original_get_security = mock_trading_context.security_provider.get_security

    async def mock_get_security(symbol):
        if symbol == "AAPL":
            security = await original_get_security(symbol)
            # Override the symbol to create a mismatch
            security.symbol = "MISMATCH"
            return security
        return await original_get_security(symbol)

    with patch.object(mock_trading_context.security_provider, "get_security", mock_get_security):
        # Try to get next symbol - should raise ValueError
        with pytest.raises(ValueError, match="Current security symbol does not match current symbol"):
            asyncio.run(mock_trading_context.next_symbol())


def test_next_symbol_position_symbol_mismatch(mock_trading_context: TradingContext):
    """Test error when position's symbol doesn't match current symbol."""

    async def mock_get_position(symbol):
        position = MagicMock()
        position.symbol = "MISMATCH"
        return position

    with patch.object(mock_trading_context.broker, "get_position", mock_get_position):
        # Try to get next symbol - should raise ValueError
        with pytest.raises(ValueError, match="Current position symbol does not match current symbol"):
            asyncio.run(mock_trading_context.next_symbol())


def test_get_value_for_identifier_no_current_symbol(mock_trading_context: TradingContext):
    """Test error when retrieving value without current symbol set."""
    with pytest.raises(ValueError, match="Current symbol is not set"):
        asyncio.run(mock_trading_context.get_value_for_identifier(ContextIdentifier.CURRENT_PRICE))


def test_get_value_for_identifier_no_current_security(mock_trading_context: TradingContext):
    """Test error when retrieving value without current security set."""
    # Set current_symbol but leave current_security as None
    mock_trading_context.current_symbol = "AAPL"
    mock_trading_context.current_security = None

    with pytest.raises(ValueError, match="Current security is not set"):
        asyncio.run(mock_trading_context.get_value_for_identifier(ContextIdentifier.CURRENT_PRICE))


def test_invalid_context_identifier(prepared_trading_context: TradingContext):
    """Test passing an invalid identifier."""
    invalid_identifier = "INVALID_IDENTIFIER"
    with pytest.raises(ValueError, match=f"Invalid context identifier"):
        asyncio.run(prepared_trading_context.get_value_for_identifier(invalid_identifier))


@pytest.mark.parametrize(
    "identifier,timeframe,should_succeed",
    [
        (ContextIdentifier.MA5, Timeframe.d5, True),
        (ContextIdentifier.MA20, Timeframe.d20, False),
        (ContextIdentifier.MA50, Timeframe.d50, False),
        (ContextIdentifier.MA100, Timeframe.d100, False),
        (ContextIdentifier.MA200, Timeframe.d200, False),
    ],
)
def test_get_moving_averages(prepared_trading_context: TradingContext, identifier, timeframe, should_succeed):
    """Test moving average retrieval behavior."""
    if should_succeed:
        # Test successful case (MA5)
        expected_value = prepared_trading_context.current_security.compute_moving_average(timeframe)
        value = asyncio.run(prepared_trading_context.get_value_for_identifier(identifier))
        assert value == expected_value.amount
    else:
        # Test failure cases (MA20-MA200)
        with pytest.raises(MissingContextValue):
            asyncio.run(prepared_trading_context.get_value_for_identifier(identifier))


@pytest.mark.parametrize(
    "identifier,timeframe,should_succeed",
    [
        (ContextIdentifier.AV5, Timeframe.d5, True),
        (ContextIdentifier.AV20, Timeframe.d20, False),
        (ContextIdentifier.AV50, Timeframe.d50, False),
        (ContextIdentifier.AV100, Timeframe.d100, False),
        (ContextIdentifier.AV200, Timeframe.d200, False),
    ],
)
def test_get_average_volume_identifier(prepared_trading_context: TradingContext, identifier, timeframe, should_succeed):
    """Test successful retrieval of average volume values."""
    if should_succeed:
        # Test successful case (AV5)
        expected_value = prepared_trading_context.current_security.compute_average_volume(timeframe)
        value = asyncio.run(prepared_trading_context.get_value_for_identifier(identifier))
        assert value == expected_value
    else:
        with pytest.raises(MissingContextValue):
            asyncio.run(prepared_trading_context.get_value_for_identifier(identifier))


@pytest.mark.parametrize(
    "identifier",
    [
        ContextIdentifier.AV5,
        ContextIdentifier.AV20,
        ContextIdentifier.AV50,
        ContextIdentifier.AV100,
        ContextIdentifier.AV200,
    ],
)
def test_get_average_volume_none_value(prepared_trading_context: TradingContext, identifier):
    """Test behavior when average volume computation returns None."""
    # Mock the compute_average_volume method to return None
    with patch.object(Security, "compute_average_volume", return_value=None):
        # Attempt to get the value - should raise MissingContextValue
        with pytest.raises(
            MissingContextValue, match=f"Average volume for {prepared_trading_context.current_symbol} is not available"
        ):
            asyncio.run(prepared_trading_context.get_value_for_identifier(identifier))

def test_get_current_volume(prepared_trading_context: TradingContext):
    """Test successful retrieval of current volume."""
    # Configure security's current bar to have a volume
    expected_volume = 15000
    prepared_trading_context.current_security.current_bar.volume = expected_volume

    # Get the current volume
    value = asyncio.run(prepared_trading_context.get_value_for_identifier(ContextIdentifier.CURRENT_VOLUME))

    # Verify correct value was returned
    assert value == Decimal(expected_volume)


def test_get_current_volume_none_value(prepared_trading_context: TradingContext):
    """Test behavior when current_bar.volume is None."""
    # Store original volume to restore later
    original_volume = prepared_trading_context.current_security.current_bar.volume

    try:
        # Set volume to None
        prepared_trading_context.current_security.current_bar.volume = None

        # Attempt to get the current volume - should raise MissingContextValue
        with pytest.raises(
            MissingContextValue, match=f"Current volume for {prepared_trading_context.current_symbol} is not available"
        ):
            asyncio.run(prepared_trading_context.get_value_for_identifier(ContextIdentifier.CURRENT_VOLUME))
    finally:
        # Restore original volume
        prepared_trading_context.current_security.current_bar.volume = original_volume


def test_get_current_price(prepared_trading_context: TradingContext):
    """Test successful retrieval of current price."""
    # Get the current price
    value = asyncio.run(prepared_trading_context.get_value_for_identifier(ContextIdentifier.CURRENT_PRICE))

    # Verify correct value was returned - should match the current_bar.close.amount
    assert value == prepared_trading_context.current_security.current_bar.close.amount


def test_get_current_price_none_value(prepared_trading_context: TradingContext):
    """Test behavior when current_bar.close is None."""
    # Store original close price to restore later
    original_close = prepared_trading_context.current_security.current_bar.close

    try:
        # Set close to None
        prepared_trading_context.current_security.current_bar.close = None

        # Attempt to get the current price - should raise MissingContextValue
        with pytest.raises(
            MissingContextValue, match=f"Current price for {prepared_trading_context.current_symbol} is not available"
        ):
            asyncio.run(prepared_trading_context.get_value_for_identifier(ContextIdentifier.CURRENT_PRICE))
    finally:
        # Restore original close price
        prepared_trading_context.current_security.current_bar.close = original_close

def test_get_account_exposure(prepared_trading_context: TradingContext):
    """Test successful retrieval of account exposure."""
    # Configure broker to return a value for account exposure
    expected_exposure = Decimal("0.45")

    # Create a patch for the broker method
    with patch.object(
        prepared_trading_context.broker, "get_account_exposure", AsyncMock(return_value=expected_exposure)
    ):
        # Get the account exposure
        value = asyncio.run(prepared_trading_context.get_value_for_identifier(ContextIdentifier.ACCOUNT_EXPOSURE))

        # Verify correct value was returned
        assert value == expected_exposure


def test_get_account_exposure_none_value(prepared_trading_context: TradingContext):
    """Test behavior when broker returns None for account exposure."""
    # Create a patch for the broker method
    with patch.object(prepared_trading_context.broker, "get_account_exposure", AsyncMock(return_value=None)):
        # Attempt to get the account exposure - should raise MissingContextValue
        with pytest.raises(MissingContextValue, match="Account exposure is not available"):
            asyncio.run(prepared_trading_context.get_value_for_identifier(ContextIdentifier.ACCOUNT_EXPOSURE))


def test_get_number_of_open_positions(prepared_trading_context: TradingContext):
    """Test successful retrieval of number of open positions."""
    # Configure broker to return positions
    positions = {"AAPL": MagicMock(), "MSFT": MagicMock(), "GOOG": MagicMock()}

    # Create a patch for the broker method
    with patch.object(prepared_trading_context.broker, "get_positions", AsyncMock(return_value=positions)):
        # Get the number of open positions
        value = asyncio.run(
            prepared_trading_context.get_value_for_identifier(ContextIdentifier.NUMBER_OF_OPEN_POSITIONS)
        )

        # Verify correct value was returned
        assert value == Decimal(len(positions))


def test_get_number_of_open_positions_none_value(prepared_trading_context: TradingContext):
    """Test behavior when broker returns None for positions."""
    # Create a patch for the broker method
    with patch.object(prepared_trading_context.broker, "get_positions", AsyncMock(return_value=None)):
        # Attempt to get the number of open positions - should raise MissingContextValue
        with pytest.raises(MissingContextValue, match="Number of open positions is not available"):
            asyncio.run(prepared_trading_context.get_value_for_identifier(ContextIdentifier.NUMBER_OF_OPEN_POSITIONS))


def test_get_available_cash(prepared_trading_context: TradingContext):
    """Test successful retrieval of available cash."""
    # Configure broker to return a value for available cash
    expected_cash = Money(amount=Decimal("25000.00"))

    # Create a patch for the broker method
    with patch.object(prepared_trading_context.broker, "get_available_cash", AsyncMock(return_value=expected_cash)):
        # Get the available cash
        value = asyncio.run(prepared_trading_context.get_value_for_identifier(ContextIdentifier.AVAILABLE_CASH))

        # Verify correct value was returned
        assert value == expected_cash.amount


def test_get_available_cash_none_value(prepared_trading_context: TradingContext):
    """Test behavior when broker returns None for available cash."""
    # Create a patch for the broker method
    with patch.object(prepared_trading_context.broker, "get_available_cash", AsyncMock(return_value=None)):
        # Attempt to get the available cash - should raise MissingContextValue
        with pytest.raises(MissingContextValue, match="Available cash is not available"):
            asyncio.run(prepared_trading_context.get_value_for_identifier(ContextIdentifier.AVAILABLE_CASH))


def test_get_average_cost(prepared_trading_context: TradingContext):
    """Test successful retrieval of average cost from position."""
    # Set up position with average cost
    expected_cost = Money(amount=Decimal("142.50"))
    position = MagicMock()
    position.average_cost = expected_cost

    # Save the original position to restore later
    original_position = prepared_trading_context.current_position

    try:
        prepared_trading_context.current_position = position

        # Get the average cost
        value = asyncio.run(prepared_trading_context.get_value_for_identifier(ContextIdentifier.AVERAGE_COST))

        # Verify correct value was returned
        assert value == expected_cost.amount
    finally:
        # Restore original position
        prepared_trading_context.current_position = original_position


def test_get_average_cost_no_position(prepared_trading_context: TradingContext):
    """Test behavior when current_position is None."""
    # Save the original position to restore later
    original_position = prepared_trading_context.current_position

    try:
        # Set current_position to None
        prepared_trading_context.current_position = None

        # Attempt to get the average cost - should raise MissingContextValue
        with pytest.raises(MissingContextValue, match="Average cost is not available as no position is open"):
            asyncio.run(prepared_trading_context.get_value_for_identifier(ContextIdentifier.AVERAGE_COST))
    finally:
        # Restore original position
        prepared_trading_context.current_position = original_position


def test_get_average_cost_none_value(prepared_trading_context: TradingContext):
    """Test behavior when position.average_cost is None."""
    # Set up position with None average cost
    position = MagicMock()
    position.average_cost = None

    # Save the original position to restore later
    original_position = prepared_trading_context.current_position

    try:
        prepared_trading_context.current_position = position

        # Attempt to get the average cost - should raise MissingContextValue
        with pytest.raises(MissingContextValue, match="Average cost is not available"):
            asyncio.run(prepared_trading_context.get_value_for_identifier(ContextIdentifier.AVERAGE_COST))
    finally:
        # Restore original position
        prepared_trading_context.current_position = original_position

def test_full_workflow_integration(mock_trading_context: TradingContext):
    """Test the full workflow of processing symbols and retrieving values."""
    # Get total number of symbols to process (limit to 1 for test performance)
    symbols_to_process = min(1, len(mock_trading_context.symbol_stack))

    # Process symbols
    for i in range(symbols_to_process):
        # Advance to the next symbol
        result = asyncio.run(mock_trading_context.next_symbol())
        assert result is True

        # Test get_value_for_identifier with different identifiers using patches

        # Test moving average
        with patch.object(Security, "compute_moving_average", return_value=Money(amount=Decimal("150"))):
            ma_value = asyncio.run(mock_trading_context.get_value_for_identifier(ContextIdentifier.MA20))
            assert ma_value == Decimal("150")

        # Test average volume
        with patch.object(Security, "compute_average_volume", return_value=50000):
            av_value = asyncio.run(mock_trading_context.get_value_for_identifier(ContextIdentifier.AV50))
            assert av_value == Decimal("50000")

        # Test current price and volume (these should work without patching)
        close_value = asyncio.run(mock_trading_context.get_value_for_identifier(ContextIdentifier.CURRENT_PRICE))
        assert isinstance(close_value, Decimal)

        # Test broker-related values
        with patch.object(
            mock_trading_context.broker, "get_account_exposure", AsyncMock(return_value=Decimal("0.3"))
        ), patch.object(
            mock_trading_context.broker,
            "get_positions",
            AsyncMock(return_value={"AAPL": MagicMock(), "MSFT": MagicMock()}),
        ), patch.object(
            mock_trading_context.broker, "get_available_cash", AsyncMock(return_value=Money(amount=Decimal("50000")))
        ):
            exp_value = asyncio.run(mock_trading_context.get_value_for_identifier(ContextIdentifier.ACCOUNT_EXPOSURE))
            assert exp_value == Decimal("0.3")

            pos_count = asyncio.run(
                mock_trading_context.get_value_for_identifier(ContextIdentifier.NUMBER_OF_OPEN_POSITIONS)
            )
            assert pos_count == Decimal("2")

            cash_value = asyncio.run(mock_trading_context.get_value_for_identifier(ContextIdentifier.AVAILABLE_CASH))
            assert cash_value == Decimal("50000")


def test_error_handling_and_recovery(mock_trading_context: TradingContext):
    """Test that errors are properly handled and context can continue processing."""
    # Get the initial symbols
    symbols = mock_trading_context.symbol_stack.copy()
    if len(symbols) <= 1:
        pytest.skip("Not enough symbols to test error handling")

    # Configure security provider to raise an exception for a specific symbol
    original_get_security = mock_trading_context.security_provider.get_security

    async def mock_get_security(symbol):
        if symbol == symbols[0]:
            raise ValueError(f"Simulated error for {symbol}")
        return await original_get_security(symbol)

    # Replace get_security with our mock
    with patch.object(mock_trading_context.security_provider, "get_security", mock_get_security):
        # First symbol should cause an error
        with pytest.raises(ValueError, match=f"Simulated error for {symbols[0]}"):
            asyncio.run(mock_trading_context.next_symbol())

        # Next symbol should succeed
        result = asyncio.run(mock_trading_context.next_symbol())
        assert result is True
        assert mock_trading_context.current_symbol == symbols[1]
        assert mock_trading_context.current_security is not None
