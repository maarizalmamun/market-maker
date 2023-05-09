
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
