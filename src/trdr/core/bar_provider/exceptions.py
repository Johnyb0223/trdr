class BarValidationException(Exception):
    pass


class BarProviderException(Exception):
    pass


class DataSourceException(BarProviderException):
    pass


class NoBarsForSymbolException(DataSourceException):
    symbol: str

    def __init__(self, symbol: str):
        self.symbol = symbol

    def __str__(self):
        return f"No bars found for symbol: {self.symbol}"


class TimeframeNotSupportedException(BarProviderException):
    pass


class InsufficientBarsException(BarProviderException):
    pass
