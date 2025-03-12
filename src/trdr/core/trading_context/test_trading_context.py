import pytest
import asyncio

from trdr.core.trading_context.trading_context import TradingContext


# Test cases for TradingContext

"""
TradingContext Test Cases

This file contains ideas for test cases covering the TradingContext class.
These test cases are organized by method and cover both happy paths and edge cases.
"""

# -----------------------------------------------------------------------------
# Creation and Initialization Tests
# -----------------------------------------------------------------------------


def test_trading_context_direct_initialization_raises_type_error(security_provider_with_fake_data, mock_broker):
    with pytest.raises(TypeError):
        TradingContext(security_provider_with_fake_data, mock_broker)


def test_trading_context_creation_with_factory_method(mock_trading_context: TradingContext):
    assert mock_trading_context is not None
    assert mock_trading_context.symbol_stack is not None
    assert mock_trading_context.current_symbol is None
    assert mock_trading_context.current_position is None
    assert mock_trading_context.current_security is None

    set_of_symbols = set(mock_trading_context.symbol_stack)
    assert set_of_symbols == set(mock_trading_context.security_provider._bar_provider._data_cache.keys())
    assert set_of_symbols == set(mock_trading_context.security_provider._bar_provider.get_symbols())


# -----------------------------------------------------------------------------
# next_symbol() Method Tests
# -----------------------------------------------------------------------------


# Test case: Successfully advancing to next symbol
# - Initialize context with multiple symbols
# - Call next_symbol()
# - Verify current_symbol, current_position, current_security are set
# - Verify return value is True
def test_trading_context_next_symbol(mock_trading_context: TradingContext):
    assert mock_trading_context.current_symbol is None
    assert mock_trading_context.current_position is None
    assert mock_trading_context.current_security is None
    asyncio.run(mock_trading_context.next_symbol())
    list_of_symbols = asyncio.run(mock_trading_context.security_provider.get_symbols())
    assert mock_trading_context.current_symbol == list_of_symbols[0]
    assert mock_trading_context.current_position is None


# Test case: Successfully processing all symbols
# - Initialize context with multiple symbols
# - Call next_symbol() until all symbols processed
# - Verify last call returns True and second-to-last symbol is set
# - Verify subsequent call returns False and resets current values to None

# Test case: Empty symbol list
# - Initialize context with empty symbol list
# - Call next_symbol()
# - Verify returns False and current values are None

# Test case: Symbol mismatch between security and current_symbol
# - Mock security_provider to return security with different symbol
# - Verify ValueError is raised with correct message
# - Verify tracer recorded exception and set status to ERROR

# Test case: Symbol mismatch between position and current_symbol
# - Mock broker to return position with different symbol
# - Verify ValueError is raised with correct message
# - Verify tracer recorded exception and set status to ERROR

# -----------------------------------------------------------------------------
# get_value_for_identifier() Method Tests
# -----------------------------------------------------------------------------

# Test case: Retrieving values when current_symbol is None
# - Initialize context but don't call next_symbol()
# - Call get_value_for_identifier() with any identifier
# - Verify ValueError is raised with correct message

# Test case: Retrieving values when current_security is None
# - Initialize context with mocked security_provider that returns None
# - Call next_symbol() and then get_value_for_identifier()
# - Verify ValueError is raised with correct message

# Test cases for Moving Average identifiers (MA5, MA20, etc.)
# - Test successful retrieval for each MA identifier
# - Test when moving average is None (raises MissingContextValue)
# - Verify tracer events and status codes

# Test cases for Average Volume identifiers (AV5, AV20, etc.)
# - Test successful retrieval for each AV identifier
# - Test when average volume is None (raises MissingContextValue)
# - Verify tracer events and status codes

# Test case: Retrieving CURRENT_VOLUME
# - Test successful retrieval
# - Test when current_bar.volume is None (raises MissingContextValue)
# - Verify tracer events and status codes

# Test case: Retrieving CURRENT_PRICE
# - Test successful retrieval
# - Test when current_bar.close is None (raises MissingContextValue)
# - Verify tracer events and status codes

# Test case: Retrieving ACCOUNT_EXPOSURE
# - Test successful retrieval from broker
# - Test when broker returns None (raises MissingContextValue)
# - Verify tracer events and status codes

# Test case: Retrieving NUMBER_OF_OPEN_POSITIONS
# - Test successful retrieval from broker
# - Test when broker returns None (raises MissingContextValue)
# - Verify tracer events and status codes

# Test case: Retrieving AVAILABLE_CASH
# - Test successful retrieval from broker
# - Test when broker returns None (raises MissingContextValue)
# - Verify tracer events and status codes

# Test case: Retrieving AVERAGE_COST
# - Test successful retrieval when position exists
# - Test when current_position is None (raises MissingContextValue)
# - Test when average_cost is None (raises MissingContextValue)
# - Verify tracer events and status codes

# Test case: Invalid identifier
# - Call get_value_for_identifier() with invalid identifier
# - Verify ValueError is raised with correct message
# - Verify tracer recorded exception and set status to ERROR

# -----------------------------------------------------------------------------
# Integration Tests
# -----------------------------------------------------------------------------

# Test case: Full workflow integration
# - Initialize context with multiple symbols
# - Iterate through all symbols with next_symbol()
# - For each symbol, retrieve multiple context values
# - Verify all operations complete successfully

# Test case: Error handling and recovery
# - Initialize context with symbols that will trigger errors
# - Verify errors are properly caught and handled
# - Verify context can continue processing remaining symbols

# -----------------------------------------------------------------------------
# Mock Design Notes
# -----------------------------------------------------------------------------

# Security Provider Mock should:
# - Return predefined list of symbols
# - Return Security objects with predefined moving averages and volumes
# - Allow control over error conditions

# Broker Mock should:
# - Return predefined positions and account values
# - Allow control over error conditions

# OpenTelemetry Mock should:
# - Record spans, events, and attributes
# - Allow verification of tracing behavior
