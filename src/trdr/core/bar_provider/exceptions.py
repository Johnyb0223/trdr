class BarValidationException(Exception):
    pass


class BarProviderException(Exception):
    pass


class SymbolNotSupportedException(BarProviderException):
    pass


class TimeframeNotSupportedException(BarProviderException):
    pass
