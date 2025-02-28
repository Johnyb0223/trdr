class BrokerException(Exception):
    pass


class BrokerInitializationException(BrokerException):
    pass


class PDTStrategyException(BrokerException):
    pass


class PDTRuleViolationException(PDTStrategyException):
    """Exception raised when a PDT rule would be violated by an action."""
    pass
