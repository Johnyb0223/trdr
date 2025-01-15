from enum import Enum

class Timeframe(Enum):
    M1 = 60        # 1 minute in seconds
    M5 = 300       # 5 minutes
    M15 = 900      # 15 minutes
    M30 = 1800     # 30 minutes
    H1 = 3600      # 1 hour
    H4 = 14400     # 4 hours
    D1 = 86400     # 1 day