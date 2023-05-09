from abc import ABC, abstractmethod
from typing import Any, Dict, List
from driftpy.constants.numeric_constants import BASE_PRECISION,PRICE_PRECISION, QUOTE_PRECISION,PEG_PRECISION, FUNDING_RATE_PRECISION

import sys
from pathlib import Path
# Get the absolute path of the directory containing this file
base_path = Path(__file__).resolve().parent
print(base_path)
# Add the parent directory (which contains the 'src' directory) to the system path
sys.path.append(str(base_path.parent))
# Import the constants module from the 'src' directory
from src import *
from driftclient import Orders, MMOrder, DriftClient
from driftpy.types import *

from utils import fetch_javascript_json

""" LV 1 MARKET MAKER - RISK MANAGEMENT FIXED/BINARY"""
# BASE PARAMETERS
MAX_TARGET = 100
MAX_LEVERAGE  = 2.0     
AGGRESSION  = 0.001 
MAX_ORDERS = 3
AGG_BAND = [0.8, 1.01]
# BASE DERISK/UPRISK THRESHOLDS (% OF LIMIT)
DERISK_TARGET = 0.8
DERISK_LEVERAGE = 0.8
UPRISK_TARGET = 0.3
UPRISK_LEVERAGE = 0.3


#class BaseStrategy(ABC):
class DefaultStrategy():
    
    """Abstract base class for market-making strategy implementations.

    This class defines the interface for a market-making strategy, which must 
    be implemented by any concrete strategy class. A strategy should implement the `execute` 
    method, which takes in a set of input data and returns a list of
    MMOrder objects representing the orders to be placed in the market.

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

    """

    def __init__(self, dlob_data: List[Dict[str, Any]], user_data: Dict[str, Any], 
                 market_data: Dict[str, Any], accaddress: 'str', custom_signals: Any = None):
        self.dlob_data = dlob_data
        self.user_data = user_data
        self.market_data = market_data
        self.custom_signals = custom_signals
        self.strat_complexity: int = 1
        # RISK VARS
        self.targetcap = MAX_TARGET
        self.levcap = MAX_LEVERAGE
        self.agg = AGGRESSION
        self.funding_rate = market_data['last_funding_rate']
        self.address = accaddress
        # BASE VARS
        try:
            user_data['leverage']
            self.current_leverage = user_data['leverage']
            self.user_position: user_data['user_position']
            self.total_collateral = user_data['total_collateral']
            self.risk = calculate_risk()
        except:
            print("No position yet. Time to enter the market!")
            self.activeTrades = False
            self.current_leverage  = None
            self.total_collateral = None 
            self.user_position = None

        def price_mark_oracle(self) -> list[float]:
            """#Orderbook calc using dlob"""
            dlob_mark = (dlob_data['best_bid'] + dlob_data['best_ask'])/2
            dlob_oracle = dlob_data['long_orders'][0]['oracle_price']
            return [dlob_mark,dlob_oracle]

        self.oracle_price = price_mark_oracle(self)[1]
        self.mark_price = price_mark_oracle(self)[0]
    
    def trade(self):
        if not self.activeTrades:
            return self.first_trade()
        else:
            return self.post_orders()

    def first_trade(self) -> Orders:
        orders = [(MMOrder(direction=PositionDirection.SHORT(), 
            order_size=(self.targetcap/2)*BASE_PRECISION, 
            offset=PRICE_PRECISION*AGGRESSION/2)),
        (MMOrder(direction=PositionDirection.SHORT(),
            order_size=(self.targetcap/3)*BASE_PRECISION, 
            offset=PRICE_PRECISION*AGGRESSION/3)),
        (MMOrder(direction=PositionDirection.SHORT(),
            order_size=(self.targetcap/6)*BASE_PRECISION, 
            offset=PRICE_PRECISION*AGGRESSION/6)),
        (MMOrder(direction=PositionDirection.LONG(),
            order_size=(self.targetcap/2)*BASE_PRECISION, 
            offset=PRICE_PRECISION*AGGRESSION/2)),
        (MMOrder(direction=PositionDirection.LONG(),
            order_size=(self.targetcap/3)*BASE_PRECISION, 
            offset=PRICE_PRECISION*AGGRESSION/3)),
        (MMOrder(direction=PositionDirection.LONG(),
            order_size=(self.targetcap/6)*BASE_PRECISION, 
            offset=PRICE_PRECISION*AGGRESSION/6))]
        return orders



    def post_orders(self) -> list[float]:    
        # = [[bidnum,bids,bid_offsets],[asknum,asks,ask_offsets]]
        #      calculate_orderspacing()[0][0]    
        oblock = calculate_orderspacing()[1]
        ordersToGo = Orders()
        for newbids in range(len(oblock[0][0])):
            transaction = MMOrder(direction=PositionDirection.LONG(),
            order_size=newbids[0][1]*BASE_PRECISION,offset=newbids[2]*PRICE_PRECISION)
            ordersToGo.add_order(transaction)

        for newasks in range(len(oblock[1][0])):
            transaction = MMOrder(direction=PositionDirection.LONG(),
            order_size=newasks[1][1]*BASE_PRECISION,offset=newasks[1]*PRICE_PRECISION)
            ordersToGo.add_order(transaction)
        return ordersToGo


    #abstractmethod
    def calculate_risk(self) -> float:
        """ 
        Determine Risk by evaluating % away from self.targetcap and % from MAX_LEVERAGE

        Args:
            - current_leverage (float)
            - MAX_LEVERAGE (2)
            - total_collateral
            - self.targetcap

        Returns:
            - curr_risk (float): goal[0.3,0.8]. Under 1 in normal circumstances. Thresholds in base 
                case work to keep this under 0.8 and increase order aggression when below 0.3. 
        """
        return max(self.current_leverage/MAX_LEVERAGE, total_collateral/self.targetcap)      
    
    #abstractmethod
    def calculate_skew(self) -> float:
        """ 
        Determine 
        
        Args:
            - current_leverage (float)
            - MAX_LEVERAGE (2)
            - total_collateral
            - self.targetcap

        Returns:
            - maxrisk (float): goal[0.3,0.8]. Under 1 in normal circumstances. Thresholds in base 
                case work to keep this under 0.8 and increase order aggression when below 0.3. 
        """
        if self.risk > UPRISK_TARGET:
            if self.user_position > 0:
                return -0.5
            else:
                return 0.5
        else:
            return 1
            

    #abstractmethod
    def calculate_aggression(self) -> list[float]:
        """In base case hardcoded to be 0.8,1.01 favouring spread
             to funding rate. Verify by evaluating order book depth + max/min

            Returns: list[float]: [bid,ask]

        """
        if self.risk < DERISK_TARGET and self.risk > UPRISK_TARGET:
            if self.funding_rate > 0 and self.oracle_price < self.mark_price:
                return [0.8,1.01]
            elif self.funding_rate < 0 and self.oracle_price > self.mark_price:
                return [1.01,0.8]
            else:
                return [1,1]
        else:
            if self.risk > DERISK_TARGET:
                return [1.2,1.2]
            else:
                if self.user_position > 0:
                    return [1.5, 0.9]
                else:
                    return [0.9,1.5]     
            return AGG_BAND           
        """or asset weight discount=(total_collateral - quote_collateral)/
            (base_collateral * mark) / 
        """

    #abstractmethod
    def calculate_ordersize(self) -> list[float]:
        """ Use parabolic spacing. Target - Current, (Target - Current)*2 """

        skew = calculate_skew() #between [-1,1] so adjusts position from 1% to 200%
        
        base_target_long = (self.targetcap - get_userpositions[1][0])*(1+skew)
        base_target_short = (self.targetcap - get_userpositions[1][1])(1+skew)

        
    #@abstractmethod
    def get_userpositions(self) -> None:
        user_orders_size = [0,0]
        user_order_count = [0,0]
        for order in self.dlob_data['long_orderbook']:
            if self.address == order["user"]:
                user_order_count[0] += order["baseAssetAmount"]
                user_order_count[0] += 1
        for order in self.dlob_data['short_orderbook']:
            if self.address == order["user"]:
                user_orders[1] += order["baseAssetAmount"]
                user_orders[1] += 1
        return [user_order_count, user_orders_size] 


    def calculate_orderspacing(self) -> list[list[float]]:
        bidnum = MAX_ORDERS - get_userpositions[0][0]
        asknum = MAX_ORDERS - get_userpositions[0][1]
        bidagg = AGGRESSION * calculate_aggression[0]
        askagg = AGGRESSION * calculate_aggression[1]

        ordersizes = calculate_ordersize() 

        bids = []
        asks = []
        bid_offsets = []
        ask_offsets = []
        bid_divider = 1
        ask_divider = 1
        counter = bidnum
        while counter > 0:
            bid_divider*= counter
            counter -= 1
            bids.append[bid_divider]
            bid_offsets[bidagg/bid_divider]

        counter = asknum
        while counter > 0:
            ask_divider*= counter
            counter -= 1
            asks.append[ask_divider]
            ask_offsets[askagg/ask_divider]

            for b in range(len(bids)):
                bids[b] = ordersizes / bids[b]
            for a in range(len(asks)):
                asks[b] = ordersizes / asks[b]

            return[[bidnum,bids,bid_offsets],[asknum,asks,ask_offsets]]
            # Make orders


    
    #@abstractmethod
    def create_orders(self) -> None:
        orders = get_userpositions()

   
    
    #@abstractmethod
    def emergency_market_order_condition(bool):
        if self.risk > 0.9:
            return True
