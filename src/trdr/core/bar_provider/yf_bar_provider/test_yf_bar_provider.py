# test to ensure the YFBarProvider throws an InsufficientBarsEception when the lookback is greater than the number of bars available

# test to ensure that the YFBarProvider throws a NoBarsForSymbolException when no bars are available for the symbol in the data cache

# test to ensure that the YFBarProvider throws a DataSourceException when the data source returns an error or no data is returned when downloading batch stock data

# lets say we pass a list of 700 tickers to the YFBarProvider and we want to 200 bars for each ticker. What happens when we fail to get bars for all tickers. It is more important to have all historic bars and the current bar for one ticker then to have 200 bars for all tickers and no current bar. We need the current bar + historic bars for a ticker to be tradable. Expected behavior would be for the bar provider to make as many (bars, current bar) pairs as it can and then notiy the caller of a failure to get bars for the remaining tickers. However this is not a ahrd failure as we can stil trade the other tickers.

# a DataSourceException should be raised if the data source returns an error or no data is returned when getting the current bar
