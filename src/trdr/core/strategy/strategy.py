from typing import Type, TypeVar, Dict, Any
from opentelemetry import trace

from ..broker.base_broker import BaseBroker
from ...dsl.dsl_loader import StrategyDSLLoader
from .models import StrategyContext, ContextIdentifier
from ..broker.models import OrderSide
from ..shared.models import Timeframe
from ..security_provider.base_security_provider import BaseSecurityProvider
from ..security_provider.models import Security
from ...dsl.dsl_ast import MissingContextValue

T = TypeVar("T", bound="Strategy")


class Strategy:
    """
    Core component for loading, evaluating, and executing trading strategies.
    
    The Strategy class is responsible for:
    1. Loading trading strategies defined in the DSL (.trdr files)
    2. Building evaluation contexts with current market and account data
    3. Evaluating entry and exit conditions against these contexts
    4. Executing trades through the broker when conditions are met
    5. Determining position sizing based on strategy rules
    
    It serves as the "brain" of the trading system, connecting market data
    (via the SecurityProvider) with execution capabilities (via the Broker)
    using rules defined in the strategy DSL.
    
    Attributes:
        strategy_file_name: Name of the .trdr file containing the strategy
        broker: Broker instance for executing trades and fetching account data
        security_provider: Provider for security objects and market data
        _tracer: OpenTelemetry tracer for instrumentation
        strategy_ast: Abstract syntax tree representing the parsed strategy
    """
    def __init__(
        self,
        strategy_file_name: str,
        broker: BaseBroker,
        security_provider: BaseSecurityProvider,
        tracer: trace.Tracer = trace.NoOpTracer(),
        _from_create: bool = False,
    ):
        if not _from_create:
            raise TypeError("Use Strategy.create() instead to create a new strategy")
        self.strategy_file_name = strategy_file_name
        self.broker = broker
        self.security_provider = security_provider
        self._tracer = tracer
        self.strategy_ast = None

    @classmethod
    async def create(
        cls: Type[T],
        strategy_file_name: str,
        broker: BaseBroker,
        security_provider: BaseSecurityProvider,
        tracer: trace.Tracer = trace.NoOpTracer(),
    ) -> T:
        """
        Factory method to create and initialize a strategy.
        
        This async factory method loads the strategy DSL file, parses it into
        an abstract syntax tree, and prepares the strategy for execution.
        
        Args:
            strategy_file_name: Name of the .trdr file containing the strategy definition
            broker: Broker instance for executing trades and getting account data
            security_provider: Provider for security objects and market data
            tracer: OpenTelemetry tracer for instrumentation
        
        Returns:
            An initialized Strategy instance ready for execution
            
        Raises:
            FileNotFoundError: If the strategy file cannot be found
            ParserError: If there are syntax errors in the strategy file
            Other exceptions depending on the specific DSL implementation
        """
        self = cls(strategy_file_name, broker, security_provider, tracer, _from_create=True)
        with self._tracer.start_as_current_span("Strategy.create") as span:
            try:
                await self._load_strategy()
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR))
                raise
            else:
                span.set_status(trace.Status(trace.StatusCode.OK))
            return self

    async def _load_strategy(self) -> None:
        with self._tracer.start_as_current_span("BaseStrategy._load_strategy") as span:
            loader = StrategyDSLLoader()
            self.strategy_ast = loader.load(self.strategy_file_name)
            span.set_attribute("strategy.ast_type", type(self.strategy_ast).__name__)

    async def build_context(self, security: Security) -> StrategyContext:
        """
        Build the evaluation context for a security by aggregating data from multiple sources.
        
        This method collects all data needed to evaluate trading decisions, including:
        - Technical indicators (moving averages, volume) from the security
        - Account information (cash, exposure) from the broker
        - Position data if the security is already held
        
        The context provides all values that can be referenced in the strategy DSL.
        
        Args:
            security: The security to build context for
            
        Returns:
            StrategyContext: A context object containing all data needed for strategy evaluation
        """
        context_data: Dict[ContextIdentifier, Any] = {}

        # Technical indicators from the security
        context_data[ContextIdentifier.MA5] = security.compute_moving_average(Timeframe.d5)
        context_data[ContextIdentifier.MA20] = security.compute_moving_average(Timeframe.d20)
        context_data[ContextIdentifier.MA50] = security.compute_moving_average(Timeframe.d50)
        context_data[ContextIdentifier.MA100] = security.compute_moving_average(Timeframe.d100)
        context_data[ContextIdentifier.MA200] = security.compute_moving_average(Timeframe.d200)
        context_data[ContextIdentifier.AV5] = security.compute_average_volume(Timeframe.d5)
        context_data[ContextIdentifier.AV20] = security.compute_average_volume(Timeframe.d20)
        context_data[ContextIdentifier.AV50] = security.compute_average_volume(Timeframe.d50)
        context_data[ContextIdentifier.AV100] = security.compute_average_volume(Timeframe.d100)
        context_data[ContextIdentifier.AV200] = security.compute_average_volume(Timeframe.d200)
        context_data[ContextIdentifier.CURRENT_VOLUME] = security.get_current_volume()
        context_data[ContextIdentifier.CURRENT_PRICE] = security.get_current_price()

        # Account data from the broker
        context_data[ContextIdentifier.ACCOUNT_EXPOSURE] = await self.broker.get_account_exposure()
        positions_dict = await self.broker.get_positions()
        context_data[ContextIdentifier.OPEN_POSITIONS] = len(positions_dict.keys())
        context_data[ContextIdentifier.AVAILABLE_CASH] = await self.broker.get_available_cash()
        
        # Position data if we already hold this security
        current_position = await self.broker.get_position(security.symbol)
        context_data[ContextIdentifier.AVERAGE_COST] = current_position.average_cost if current_position else None

        # Convert enum keys to strings for StrategyContext initialization
        flat_context = {key.value: value for key, value in context_data.items()}
        return StrategyContext(**flat_context)

    async def execute(self) -> None:
        """
        Execute the trading strategy across all available securities.
        
        This method:
        1. Cancels any pending orders to ensure a clean slate
        2. Gets all securities from the security provider
        3. For each security:
           - Builds an evaluation context with current data
           - Determines whether to:
             a. Exit an existing position (if held)
             b. Enter a new position (if not held)
           - Executes the appropriate orders through the broker
        
        The execution logic follows these rules:
        - For existing positions: Evaluate exit conditions and sell if met
        - For potential new positions: Evaluate entry conditions and buy if met
        - Position sizing is determined by the strategy's sizing rules
        
        If a required context value is missing, the security is skipped.
        """
        await self.broker._cancel_all_orders()
        list_of_securities = await self.security_provider.get_security_list()

        for security in list_of_securities:
            context = await self.build_context(security)
            current_position = await self.broker.get_position(security.symbol)
            
            # Handle existing positions - check exit conditions
            if current_position:
                try:
                    should_exit = self.strategy_ast.evaluate_exit(context)
                except MissingContextValue:
                    # Skip if required context value is missing
                    continue
                else:
                    if should_exit:
                        await self.broker.place_order(security.symbol, OrderSide.SELL, current_position.quantity)
            
            # Handle potential new positions - check entry conditions
            else:
                try:
                    should_enter = self.strategy_ast.evaluate_entry(context)
                except MissingContextValue:
                    # Skip if required context value is missing
                    continue
                else:
                    if should_enter:
                        # Get position size from strategy's sizing rules
                        dollar_amount = self.strategy_ast.evaluate_sizing(context)
                        await self.broker.place_order(security.symbol, OrderSide.BUY, dollar_amount)
