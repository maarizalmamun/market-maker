
"""
from typing import Any, Dict, List
from abc import ABC, abstractmethod

import sys
from pathlib import Path
base_path = Path(__file__).resolve().parent.parent
sys.path.append(str(base_path.parent))
from src import *
#from base_strategy import BaseStrategy
from utils import fetch_javascript_json


class DefaultStrategy(BaseStrategy):

    Abstract base class for market-making strategy implementations.
        Initializes a new instance of DefaultStrategy with the given parameters.

    This class defines the interface for a market-making strategy, which must 
    be implemented by any concrete strategy class. A strategy should implement the `execute` 
    method, which takes in a set of input data and returns a list of
    MMOrder objects representing the orders to be placed in the market.
    Args:
        address (str): The address of the strategy.
        dlob_data (list[dict]): The data for the DLOB.
        user_data (dict[str,Any]): The user account data on the exchange
        market_data (dict[str,Any]): The market data on the exchange for the given trading pair
        drift_acct(DriftClient): A DriftClient Object for interacting with the driftpy client for posting trades
        accaddress(str): User account public address
        custom_signals(Any): Any custom signal parameters for optional extendible market making data
 
    Attributes:
        market_data (dict): A dictionary containing market data, including the current price, 
        the order book, and other relevant information. It includes the following keys:
        - 'price': (float) the current market price
        - 'orderbook': (dict) the order book with bids and asks at different prices
        - 'last_price': (float) the last traded price
        - 'timestamp': (int) the timestamp of the data
        - other keys with additional market data such as volume and volatility
        user_data (dict): A dictionary containing user account data, 
        including the user's balance, position, and other relevant information. It includes the following keys:
        - 'balance': (float) the user's account balance
        - 'position': (float) the user's current position
        - 'leverage': (float) the user's current leverage
        - 'max_position_size': (float) the maximum position size the user is allowed to take
        - other keys with additional user data
        dlob_data (dict): A dictionary containing the Decentralized Limit 
          - 'best_bid': A float representing the highest bid in the orderbook
        - 'best_ask': A float representing the lowest ask in the orderbook
        - 'long_orderbook': A dictionary representing the long orderbook, with the following keys:
            - 'price': A float representing the price of the order
            - 'quantity': A float representing the quantity of the order
            - 'cumulative_quantity': A float representing the cumulative quantity of all orders at or below the current price
        - 'short_orderbook': A dictionary representing the short orderbook, with the same keys as 'long_orderbook'
        - 'long_orders': A list of dictionaries representing the top long orders, with the following keys:
            - 'orderId': A string representing the ID of the order
            - 'direction': A string representing the direction of the order ('long' or 'short')
            - 'price': A float representing the price of the order
            - 'baseAssetAmount': A float representing the quantity of the order
            - 'oracle_price': A float representing the oracle price of the order
            - 'oraclePriceOffset': A float representing the offset from the oracle price of the order
        - 'short_orders': A list of dictionaries representing the top short orders, with the same keys as 'long_orders'
        orderbook_levels (int): The number of levels to use when retrieving 
        order book data. If set to 0, only the best bid and ask prices 
        will be used. If set to -1, all available levels will be used.
        custom_signals (Any): For expanding to new strategies outside of current data scope
        strat_complexity list[bool]: Initialized strat_complexity

        Methods:
        execute: Abstract method to be implemented by concrete strategy classes. Takes in the market data, user data, 
            and DLOB data and returns a list of MMOrder objects representing the orders to be placed in the market.
    def __init__(self, dlob_data: dict, user_data: dict,
                 market_data: dict, custom_signals: Any):
        super().__init__(dlob_data, user_data, market_data, custom_signals)
        # additional initialization for this strategy
    
    def calculate_risk(self) -> float:
        # implementation for calculating risk based on data in self.dlob_data, self.user_data, and self.market_data
        return risk_value
    
    def calculate_skew(self) -> float:
        # implementation for calculating skew based on data in self.dlob_data, self.user_data, and self.market_data
        return skew_value
    
    def calculate_aggression(self) -> float:
        # implementation for calculating aggression based on data in self.dlob_data, self.user_data, and self.market_data
        return aggression_value
    
    def create_orders(self, skew: float, aggression: float, risk: float) -> None:
        # implementation for creating orders based on skew, aggression, and risk values
        # the order creation logic will be specific to this strategy
        pass
    
    def emergency_market_order_condition(self) -> bool:
        # implementation for determining whether an emergency market order is necessary
        # this logic will be specific to this strategy
        return emergency_market_order_condition




# Bigger risk: Leverage or Target Size?

#user_leverage = user_data['user_leverage']
#user_position = user_data['user_position']

#print(user_leverage, '\n', user_position)

# Run the market-making loop

# Check for order fulfillment


LV1 requires: 
Args: best_bid,best_ask,  (DLOB)
Constants

last_position = user_data[user_position]
if (not USE_MARKET_SIGNALS and not USE_MARKET_SIGNALS
and last_position == user_data[user_position]): # && len(last_position) == MAX_ORDERS * 2
continue
set_orders()
>
>
>
"""
# Get the current market data
# Update the strategy with the new market data
# Calculate the desired position size based on the updated strategy

# Apply MM logic to adjust the desired position size
#risk_adjusted_position_size = strategy.apply_risk_management(desired_position_size, positions, inventory)

# Place orders based on the new position size and updated market data
#orders = strategy.place_orders(risk_adjusted_position_size)

# Submit the orders to the clearing house

# Wait for the next loop iteration
#await asyncio.sleep(TRADE_FREQUENCY)
