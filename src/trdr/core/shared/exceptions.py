class TradingDateException(Exception):
    pass









class BrokerException(Exception):
    pass


class BrokerInitializationException(BrokerException):
    pass


class PDTStrategyException(BrokerException):
    pass
