from typing import Type, TypeVar, Dict, Any
from opentelemetry import trace

from ..broker.base_broker import BaseBroker
from ...dsl.dsl_loader import StrategyDSLLoader
from .models import StrategyContext, ContextIdentifier
from ..broker.models import OrderSide
from ..shared.models import Timeframe
from ..security_provider.base_security_provider import BaseSecurityProvider
from ..security_provider.models import Security

T = TypeVar("T", bound="Strategy")


class Strategy:
    def __init__(
        self,
        strategy_file_name: str,
        broker: BaseBroker,
        security_provider: BaseSecurityProvider,
        tracer: trace.Tracer = trace.NoOpTracer(),
        _from_create: bool = False,
    ):
        if not _from_create:
            raise TypeError("Use BaseStrategy.create() instead to create a new strategy")
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
        self = cls(strategy_file_name, broker, security_provider, tracer, _from_create=True)
        with self._tracer.start_as_current_span("BaseStrategy.create") as span:
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
        Build and validate the evaluation context (flat) by aggregating data
        from the provided Security object (from bar_provider) and the broker.
        Enum keys are used for consistency, then converted to raw string keys
        for the Pydantic model.
        """
        context_data: Dict[ContextIdentifier, Any] = {}
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
        context_data[ContextIdentifier.ACCOUNT_EXPOSURE] = await self.broker.get_account_exposure()
        positions_dict = await self.broker.get_positions()
        context_data[ContextIdentifier.OPEN_POSITIONS] = len(positions_dict.keys())
        context_data[ContextIdentifier.AVAILABLE_CASH] = await self.broker.get_available_cash()
        current_position = await self.broker.get_position(security.symbol)
        if current_position:
            context_data[ContextIdentifier.AVERAGE_COST] = current_position.average_cost
        else:
            context_data[ContextIdentifier.AVERAGE_COST] = None

        # Convert enum keys to strings for StrategyContext initialization.
        flat_context = {key.value: value for key, value in context_data.items()}
        return StrategyContext(**flat_context)

    async def execute(self) -> None:
        # cancel all currently open orders
        await self.broker._cancel_all_orders()

        # get a list of all traded securities
        list_of_securities = await self.security_provider.get_security_list()

        # evaluate the strategy for each security
        for security in list_of_securities:
            # Build context using the provided security.
            context = await self.build_context(security)

            current_position = await self.broker.get_position(security.symbol)
            if current_position:
                if self.strategy_ast.evaluate_exit(context):
                    await self.broker.place_order(security.symbol, OrderSide.SELL, current_position.quantity)
            else:
                # if we don't have a position, evaluate the entry conditions
                if self.strategy_ast.evaluate_entry(context):
                    # determine the size of the order
                    dollar_amount = self.strategy_ast.evaluate_sizing(context)
                    await self.broker.place_order(security.symbol, OrderSide.BUY, dollar_amount)
