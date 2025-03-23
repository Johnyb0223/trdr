import datetime
import pandas as pd


def fake_yf_download(*args, **kwargs):
    """
    This returns fake batch stock data for two symbols. This is what yahoo finance returns for a batch download request
    grouped by symbol over a 3 day period.
    """
    dates = pd.bdate_range(end=datetime.datetime.now(), periods=5)

    data = {
        ("AAPL", "Open"): [100, 101, 102, 103, 104],
        ("AAPL", "High"): [110, 111, 112, 113, 114],
        ("AAPL", "Low"): [90, 91, 92, 93, 94],
        ("AAPL", "Close"): [105, 106, 107, 108, 109],
        ("AAPL", "Volume"): [1000, 1100, 1200, 1300, 1400],
        ("MSFT", "Open"): [200, 201, 202, 203, 204],
        ("MSFT", "High"): [210, 211, 212, 213, 214],
        ("MSFT", "Low"): [190, 191, 192, 193, 194],
        ("MSFT", "Close"): [205, 206, 207, 208, 209],
        ("MSFT", "Volume"): [2000, 2100, 2200, 2300, 2400],
        # this is what is returned when a symbol is not found
        ("ABCDEFG", "Open"): [None, None, None, None, None],
        ("ABCDEFG", "High"): [None, None, None, None, None],
        ("ABCDEFG", "Low"): [None, None, None, None, None],
        ("ABCDEFG", "Close"): [None, None, None, None, None],
        ("ABCDEFG", "Volume"): [None, None, None, None, None],
        # this is what is returned when we hit the rate limit
        ("AMZN", "Open"): None,
        ("AMZN", "High"): None,
        ("AMZN", "Low"): None,
        ("AMZN", "Close"): None,
        ("AMZN", "Volume"): None,
    }

    return pd.DataFrame(data, index=dates)
