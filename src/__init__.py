"""Constants used throughout the project."""

# API CONSTANTS
ENV = 'devnet'
"""str: The current environment (e.g. devnet)."""

MARKET_NAME = "SOL-PERP"
"""str: The name of the market (e.g. SOL-PERP)."""

URL = 'https://api.devnet.solana.com'
"""str: The URL of the API to use."""

# DEV CONSTANTS
DEV_MODE = True
"""bool: Whether the code is currently running in development mode."""

# TRADING, SAMPLING, AND DELETION PERIODS
""" Currently trades every 12 seconds. Samples and archives to path: data/archived/ every 5*12s = 1 minute
Max data buffer of 1200 / 1min = 20 hours of data.
Although not yet utilized further developement would allow for custom signals, 
trend generation, library imports for advanced modelling, analysis, machine learning etc. """

TRADE_FREQUENCY = 12
"""int: The frequency (in seconds) at which the code should attempt to place trades."""

COLLECTION_FREQUENCY = 5
"""int: The frequency (in units of `TRADE_FREQUENCY`) at which market data should be sampled and stored."""

STORAGE_BUFFER = 1200
"""int: The maximum number of samples to store in memory before archiving them to disk."""
