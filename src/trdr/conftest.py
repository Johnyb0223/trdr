import asyncio
import pytest
import yfinance as yf
from decimal import Decimal

from .core.security_provider.security_provider import SecurityProvider
from .core.bar_provider.yf_bar_provider.yf_bar_provider import YFBarProvider
from .core.shared.models import Money
from .test_utils.fake_yf_download import fake_yf_download
from .test_utils.security_generator import SecurityGenerator, Criteria
from .core.broker.mock_broker.mock_broker import MockBroker
from .core.broker.pdt.wiggle_strategy import WiggleStrategy
from .core.broker.pdt.yolo_strategy import YoloStrategy
from .core.broker.models import Position, PositionSide
from .core.trading_engine.trading_engine import TradingEngine


@pytest.fixture(scope="function")
def yf_bar_provider_with_fake_data(monkeypatch):
    monkeypatch.setattr(yf, "download", fake_yf_download)
    monkeypatch.setattr(yf.shared, "_ERRORS", {"ABCDEFG": "YFTzMissingError()", "AMZN": "JSONDecodeError()"})
    return asyncio.run(YFBarProvider.create(["AAPL", "MSFT", "ABCDEFG", "AMZN"]))


@pytest.fixture(scope="function")
def security_provider_with_fake_data(yf_bar_provider_with_fake_data):
    return asyncio.run(SecurityProvider.create(yf_bar_provider_with_fake_data))


@pytest.fixture(scope="function")
def random_security(symbol="AAPL", count=200):
    """Create a random security with the given symbol and bar count.

    Args:
        symbol: The ticker symbol to use
        count: The number of bars to generate

    Returns:
        A Security instance with randomly generated price and volume data
    """
    generator = SecurityGenerator(Criteria(count=count))
    security = generator.find_suitable_security()
    # Override the symbol if requested
    if symbol != security.symbol:
        security.symbol = symbol
    return security


@pytest.fixture(scope="function")
def get_random_security():
    """Legacy fixture name for backward compatibility."""
    generator = SecurityGenerator(Criteria(count=200))
    return generator.find_suitable_security()


@pytest.fixture(scope="module")
def security_generator():
    """Return a configured SecurityGenerator instance."""
    return SecurityGenerator(Criteria(count=200))


@pytest.fixture(scope="function")
def dummy_position(symbol="AAPL"):
    """Create a test position with default values."""
    return Position(
        symbol=symbol,
        quantity=Decimal(10),
        average_cost=Money(amount=Decimal(100)),
        side=PositionSide.LONG,
    )


@pytest.fixture(scope="function")
def dummy_positions(dummy_position):
    """Create a dictionary of test positions."""
    positions = {
        "AAPL": dummy_position,
        "MSFT": Position(
            symbol="MSFT",
            quantity=Decimal(5),
            average_cost=Money(amount=Decimal(200)),
            side=PositionSide.LONG,
        ),
    }
    return positions


@pytest.fixture(scope="function")
def mock_broker():
    broker = asyncio.run(MockBroker.create())
    yield broker
    asyncio.run(broker._session.close())


@pytest.fixture(scope="function")
def mock_broker_with_wiggle_strategy():
    pdt_strategy = WiggleStrategy.create()
    pdt_strategy.wiggle_room = 2
    broker = asyncio.run(MockBroker.create(pdt_strategy=pdt_strategy))
    yield broker
    asyncio.run(broker._session.close())


@pytest.fixture(scope="function")
def mock_broker_with_yolo_strategy():
    pdt_strategy = YoloStrategy.create()
    broker = asyncio.run(MockBroker.create(pdt_strategy=pdt_strategy))
    yield broker
    asyncio.run(broker._session.close())


@pytest.fixture(scope="function")
def mock_trading_engine(mock_broker, security_provider_with_fake_data):
    engine = asyncio.run(
        TradingEngine.create(
            "test_strat.trdr",
            mock_broker,
            security_provider_with_fake_data,
            strategies_dir="src/trdr/test_utils/strategies",
        )
    )
    return engine


@pytest.fixture(scope="function")
def mock_trading_engine_always_buy(mock_broker, security_provider_with_fake_data):
    engine = asyncio.run(
        TradingEngine.create(
            "always_buy.trdr",
            mock_broker,
            security_provider_with_fake_data,
            strategies_dir="src/trdr/test_utils/strategies",
        )
    )
    return engine


@pytest.fixture(scope="function")
def mock_trading_engine_always_sell(mock_broker, security_provider_with_fake_data):
    engine = asyncio.run(
        TradingEngine.create(
            "always_sell.trdr",
            mock_broker,
            security_provider_with_fake_data,
            strategies_dir="src/trdr/test_utils/strategies",
        )
    )
    return engine
