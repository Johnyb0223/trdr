class PortfolioException(Exception):
    pass


class PositionNotFoundException(PortfolioException):
    pass


class OrderNotFoundException(PortfolioException):
    pass
