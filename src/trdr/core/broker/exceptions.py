class BrokerException(Exception):
    """Base class for broker exceptions."""


class BrokerInitializationException(BrokerException):
    """Exception raised when broker initialization fails."""
