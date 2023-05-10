from abc import ABC, abstractmethod
from typing import Any, Dict, List

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
AGG_SKEW = [0.8, 1.01]
# BASE DERISK/UPRISK THRESHOLDS (% OF LIMIT)
DERISK_TARGET = 0.8
DERISK_LEVERAGE = 0.8
UPRISK_TARGET = 0.3
UPRISK_LEVERAGE = 0.3


#class BaseStrategy(ABC):
class DefaultStrategy():
    
    """Abstract base class for market-making strategy implementations.
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
    """

    def __init__(self, dlob_data: List[Dict[str, Any]], user_data: Dict[str, Any], 
                 market_data: Dict[str, Any], drift_acct: DriftClient, accaddress: 'str', custom_signals: Any = None):
        self.dlob_data = dlob_data
        self.user_data = user_data
        self.market_data = market_data
        self.drift_acct = drift_acct
        self.custom_signals = custom_signals
        self.strat_complexity: int = 1

        # RISK VARS
        self.targetcap = MAX_TARGET
        self.levcap = MAX_LEVERAGE
        self.agg = AGGRESSION
        self.funding_rate = market_data['last_funding_rate']
        self.address = accaddress
        self.derisk = DERISK_TARGET
        self.uprisk = UPRISK_TARGET
        self.agg_skew = AGG_SKEW
        self.max_orders = MAX_ORDERS
        self.oracle_price = self.dlob_data['long_orders'][0]['oracle_price']
        self.mark_price = (self.dlob_data['best_bid'] + self.dlob_data['best_ask'])/2

        # BASE VARS
        try:
            self.user_position: user_data['user_position']
            self.activeTrades = True
            self.current_leverage = user_data['leverage']
            self.total_collateral = user_data['total_collateral']
            self.risk = calculate_risk()
        except:
            print("No position yet. Time to enter the market!")
            self.user_position = None
            self.activeTrades = False
            self.current_leverage  = 0
            self.total_collateral = None
            self.risk = 0

    def get_userpositions(self) -> list[float]:
        """Get user's long and short positions
        
        Returns:
            user_positions: list[float]: User open order Bid and Asks, quantity and amount
                [num_long_trades,num_short_trades],[sum_long_trades, sum_short_trades]
        """
        if self.activeTrades == False:
            return [[0,0],[0,0]]
        else:
            user_order_count = [0,0]
            user_order_size = [0,0]
            for order in self.dlob_data['long_orderbook']:
                if self.address == order["user"]:
                    user_order_size[0] += order["baseAssetAmount"]
                    user_order_count[0] += 1
            for order in self.dlob_data['short_orderbook']:
                if self.address == order["user"]:
                    user_order_size[1] += order["baseAssetAmount"]
                    user_order_count[1] += 1
            print("User positions are:", user_order_count, user_order_size)
            return [user_order_count, user_order_size]  

    def calculate_risk(self) -> float:
        """Calculate current positions level of risk based on given risk management parameters
        Returns:
            - risk (float): Current position % to max risk threshold
            goal[0.3,0.8]. Under 1 in normal circumstances. 
            Thresholds in default case work to keep this under 0.8 and 
            increase order aggression when below 0.3. 
        """
        risk =  max(self.current_leverage/self.levcap, self.total_collateral/self.targetcap)      
        print("risk is: ", risk)
        return risk

    def calculate_funding_adjustment(self) -> int:
        """Main factor to determine which way position skew lies
        
        Returns:
            adjustment_factor (int): 
            Positive indicates funding favours shorts
            Negative indicates funding favours longs
        """
        if self.funding_rate > 0 and self.oracle_price < self.mark_price:
            return 1.0
        elif self.funding_rate < 0 and self.oracle_price > self.mark_price:
            return -1.0
        elif self.oracle_price < self.mark_price:
            return 0.5
        elif self.oracle_price > self.mark_price:
            return -0.5
        else:
            return 0.0

    def calculate_skew_factor(self) -> float:
        """Calculates skew that can vary from -1 to 1
            In our case it ranges from -0.5 to 0.5 (Can't ever have only one sided only order placement)
        Returns:
            - maxrisk (float): goal[0.3,0.8]. Under 1 in normal circumstances. Thresholds in base 
                case work to keep this under 0.8 and increase order aggression when below 0.3. 
        """
        # Funding adjustment
        skew = float(calculate_funding_adjustment()) * 0.25

        # Risk mode: Derisk position
        if self.risk > self.uprisk:
            # Risk adjustment
            if self.user_position > 0:
                skew += -0.5
            else:
                skew += 0.5
        return skew

    def calculate_aggression_factor(self) -> list[float]:
        """Calculate aggression based on the current state of the market.
        In base case hardcoded to be 0.8,1.01 favouring spread
             to funding rate. Verify by evaluating order book depth + max/min

            Returns: list[float]: [bid,ask]
        self.agg * self.agg_skew[0] or [1]
        """
        funding = self.funding_rate
        if (self.risk < self.uprisk):
            if funding == 0:
                return [1.0,1.0]
            if self.risk > self.derisk:
                # Normal conditions, not in derisk or uprisk mode
                if funding > 0:
                    return [1 - funding*abs(1- self.agg_skew[0]), 1 + funding*abs(1- self.agg_skew[1])]
                else:
                    return [1 + funding*abs(1- self.agg_skew[0]), 1 - funding*abs(1- self.agg_skew[1])]
            else:
                # Lowrisk mode: increase risk by tightening aggression by 25%
                if funding > 0:
                    return [1 - funding*abs(1- self.agg_skew[0])*0.75, 1 + funding*abs(1- self.agg_skew[1])*0.75]
                else:
                    return [1 + funding*abs(1- self.agg_skew[0])*0.75, 1 - funding*abs(1- self.agg_skew[1])*0.75]            
        else:
            # Highrisk mode: decrease risk by loosening aggression to 200% of risk side
            if self.user_position > 0:
                return [2.0,1.0]
            else:
                return [1.0,2.0]    

    def calculate_ordersize(self) -> list[float,float]:
        """ Use parabolic spacing. Target - Current, (Target - Current)*2 """
        """Get user's long and short positions"""
        if self.activeTrades == False:
            return [self.targetcap, self.targetcap]
        user_order_count = [0,0]
        user_order_size = [0,0]
        if self.activeTrades == True:
            for order in self.dlob_data['long_orderbook']:
                if self.address == order["user"]:
                    user_order_size[0] += order["baseAssetAmount"]
                    user_order_count[0] += 1
            for order in self.dlob_data['short_orderbook']:
                if self.address == order["user"]:
                    user_order_size[1] += order["baseAssetAmount"]
                    user_order_count[1] += 1
        print("User positions are:", user_order_count, user_order_size)
        user_positions = self.get_userpositions()
        sum_long_trades = user_positions[1][0]
        sum_short_trades = user_positions[1][1]

        # Calculate Target Size - Active Trade sum with skew adjustment
        skew = calculate_skew_factor() 
        base_target_long = (self.targetcap - sum_long_trades)*(1.0 + skew)
        base_target_short = (self.targetcap - sum_short_trades)*(1.0 - skew)
        print("Skew is: ", skew, "Base Target Long and shorts are:", base_target_long, base_target_short)
        return [base_target_long, base_target_short]

    def calculate_order_params(self) -> list[list[float]]:
        """Calculate the spacing between the orders to be posted on the market."""
        bidagg = self.agg * self.calculate_aggression_factor()[0]
        askagg = self.agg * self.calculate_aggression_factor()[1]        
        if(self.activeTrades == False):
            bidnum = 3
            asknum = 3
        else:
            bidnum = self.max_orders - self.get_userpositions[0][0]
            asknum = self.max_orders - self.get_userpositions[0][1]
        # Total base quantity of longs and shorts to post
        bid_sizes = []
        ask_sizes = []
        bid_offsets = []
        ask_offsets = []
        
        # Configure quadratic spacing
        bid_divider = 1
        ask_divider = 1
        counter = 1
        base_target_long = self.calculate_ordersize()[0]
        base_target_short = self.calculate_ordersize()[1]
        print(f"bidnum = {bidnum}, asknum = {asknum}")
        denominator = 0
        for i in range(1, bidnum+1):
            denominator += i        
        while counter <= bidnum:
            bid_sizes.append(counter/denominator)
            bid_offsets.append(bidagg*(counter/denominator))
            counter += 1
        counter = 1
        for i in range(1, asknum+1):
            denominator += i 
        while counter <= asknum:
            ask_sizes.append(counter/denominator)
            ask_offsets.append(askagg*(counter/denominator))
            counter += 1

        for b in range(bidnum):
            bid_sizes[b] = base_target_long * bid_sizes[b]
        for a in range(asknum):
            ask_sizes[a] = base_target_short * ask_sizes[a]
        return[[bid_sizes,bid_offsets],[ask_sizes,ask_offsets]]
        # Make orders

    def trade(self):
        if not self.activeTrades:
            return self.first_trade()
        else:
            return self.post_orders()   

    def post_orders(self) -> list[float]:    
        """Post orders on the market. Returns a list of orders."""
        # Get order details from algorithm
        buy_order_params, sell_order_params = self.calculate_order_params()
        # Create Orders Object to prepare order placement
        orders = Orders(self.drift_acct)
        for i in range(len(buy_order_params[0])):
            base_amt = buy_order_params[0][i]
            offset = buy_order_params[1][i]
            order = MMOrder(direction=PositionDirection.LONG(),
            order_size=base_amt,offset=offset)
            orders.add_order(order)
        for i in range(len(sell_order_params[0])):
            base_amt = sell_order_params[0][i]
            offset = -sell_order_params[1][i]
            order = MMOrder(direction=PositionDirection.SHORT(),
            order_size=base_amt,offset=offset)
            orders.add_order(order)
        return orders
      
    def first_trade(self) -> Orders:
        """Place the initial orders to be executed by the market maker. Returns the orders. """
        orderlist = [(MMOrder(direction=PositionDirection.SHORT(), 
            order_size=(self.targetcap/2), 
            offset=AGGRESSION/2)),
        (MMOrder(direction=PositionDirection.SHORT(),
            order_size=(self.targetcap/3), 
            offset=AGGRESSION/3)),
        (MMOrder(direction=PositionDirection.SHORT(),
            order_size=(self.targetcap/6), 
            offset=AGGRESSION/6)),
        (MMOrder(direction=PositionDirection.LONG(),
            order_size=(self.targetcap/2), 
            offset=AGGRESSION/2)),
        (MMOrder(direction=PositionDirection.LONG(),
            order_size=(self.targetcap/3), 
            offset=AGGRESSION/3)),
        (MMOrder(direction=PositionDirection.LONG(),
            order_size=(self.targetcap/6), 
            offset=AGGRESSION/6))]
        orders = Orders(self.drift_acct)
        print("orderlist", orderlist)
        for i, order in enumerate(orderlist):
            orders.add_order(order)
        print((orders.orders[0].orderparams))
        return orders

    def emergency_market_order_condition(bool):
        if self.risk > 0.9:
            return True
