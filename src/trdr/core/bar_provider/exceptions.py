class BarValidationException(Exception):
    pass


class BarProviderException(Exception):
    pass


class DataSourceException(BarProviderException):
    """
    This exception represents the case where the data source returns an error other than a NoBarsForSymbolException.
    """

    pass


class NoBarsForSymbolException(DataSourceException):
    """
    This exception represents the case wehre Yahoo Fincance cannot return any data for a symbol.
    """

    symbol: str

    def __init__(self, symbol: str):
        self.symbol = symbol

    def __str__(self):
        return f"No bars found for symbol: {self.symbol}"


class TimeframeNotSupportedException(BarProviderException):
    pass


class InsufficientBarsException(BarProviderException):
    pass
