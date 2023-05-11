"""Constants used throughout the project."""
# API CONSTANTS
ENV = 'devnet'
"""str: The current environment (e.g. devnet)."""

MARKET_NAME = "SOL-PERP"
"""str: The name of the market (e.g. SOL-PERP)."""

URL = 'https://api.devnet.solana.com'
"""str: The URL of the API to use."""

# DEV CONSTANTS
DEV_MODE = False
"""bool: Whether the code is currently running in development mode. Use archived data to reduce runtime"""

# TRADING, SAMPLING, AND DELETION PERIODS
TRADE_FREQUENCY = 12
"""int: The frequency (in seconds) at which the code should attempt to place trades."""

COLLECTION_FREQUENCY = 5
"""int: The frequency (in units of `TRADE_FREQUENCY`) at which market data should be sampled and stored.
Default is 12*5 = every 60s = 1 minute
"""

STORAGE_BUFFER = 1200
"""int: The maximum number of samples to store in memory before archiving them to disk.
Default max occurs at 1200* 1min = 1200min -> 20hours
"""