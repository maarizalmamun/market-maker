import sys
from abc import ABC, abstractmethod
from typing import Any, Dict, List
from pathlib import Path

base_path = Path(__file__).resolve().parent
print(base_path)
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
    """
    Abstract base class for market-making strategy implementations.

    Args:
        dlob_data (list[dict]): The data for the DLOB.
        user_data (dict[str,Any]): The user account data on the exchange.
        market_data (dict[str,Any]): The market data on the exchange for the given trading pair.
        drift_acct(DriftClient): A DriftClient Object for interacting with the driftpy client for posting trades.
        accaddress(str): User account public address.
        custom_signals(Any): Any custom signal parameters for optional extendible market making data.

    Attributes:
        dlob_data (list[dict]): A dictionary containing the Decentralized Limit Order Book (DLOB) data.
        user_data (dict[str,Any]): A dictionary containing user account data.
        market_data (dict[str,Any]): A dictionary containing market data.
        drift_acct(DriftClient): A DriftClient object for interacting with the Drift API.
        custom_signals(Any): Any custom signal parameters for optional extendible market making data.
        strat_complexity (int): The complexity of the strategy.

    Methods:
        get_userpositions: Get user's long and short positions.
        calculate_risk: Calculate the current level of risk.
        calculate_funding_adjustment: Calculate the funding adjustment factor.
        calculate_skew_factor: Calculate the skew factor.
        calculate_aggression_factor: Calculate the aggression factor.
        calculate_ordersize: Calculate the order size.
        calculate_order_params: Calculate the order parameters.
        post_orders: Post orders on the market.
        emergency_market_order_condition: Check if an emergency market order condition is met.
    """

    def __init__(
    self,
    dlob_data: List[Dict[str, Any]],
    user_data: Dict[str, Any],
    market_data: Dict[str, Any],
    drift_acct: DriftClient,
    accaddress: str,
    custom_signals: Any = None,
    ):
        """Initializes a new instance of DefaultStrategy with the given parameters.
        
        Args:
            dlob_data (List[Dict[str, Any]]): The data for the DLOB.
            user_data (Dict[str, Any]): The user account data on the exchange.
            market_data (Dict[str, Any]): The market data on the exchange for the given trading pair.
            drift_acct (DriftClient): A DriftClient object for interacting with the driftpy client for posting trades.
            accaddress (str): User account public address.
            custom_signals (Any): Any custom signal parameters for optional extendible market making data.
        """
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
            List[float]: User open order Bid and Asks, quantity and amount
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
        """
        Calculate current position's level of risk based on given 
        risk management parameters
        
        Returns:
            float: Current position % to max risk threshold (goal[0.3,0.8])
        """
        risk =  max(self.current_leverage/self.levcap, self.total_collateral/self.targetcap)      
        print("risk is: ", risk)
        return risk

    def calculate_funding_adjustment(self) -> int:
        """Main factor to determine which way position skew lies
        
        Returns:
            int: Positive indicates funding favors shorts,
                 Negative indicates funding favors longs.
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
        """Calculates skew that can vary from -1 to 1.
           In our case, it ranges from -0.5 to 0.5.
        
        Returns:
            float: Skew value between -0.5 and 0.5.
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
        
        Returns:
            list[float]: Aggression factors for bid and ask orders.
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
        """Use parabolic spacing to calculate order sizes.
        
        Returns:
            list[float, float]: Sizes for long and short orders.
        """
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
        """Calculate the spacing between the orders to be posted on the market.
        
        Returns:
            list[list[float]]: Order sizes and offsets for bid and ask orders.
        """        
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
        print(f"Number of long Orders: = {bidnum}, Number of Short Orders: = {asknum}")
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

    def post_orders(self) -> Orders:    
        """Post orders on the market. Returns a list of orders.
        
        Returns:
            Orders: An instance of the Orders class representing the orders to be placed.
        """        
        buy_order_params, sell_order_params = self.calculate_order_params()
        if len(buy_order_params[0]) == 0:
            return None
        else:
        # Create Orders Object to prepare order placement
            orders = Orders(self.drift_acct, self.oracle_price)
            """Order class initialized with instance of ClearingHouse"""
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
        
    def emergency_market_order_condition(self) -> bool:
        """Check if an emergency market order condition is met.
        
        Returns:
            bool: True if the condition is met, False otherwise.
        """
        if self.risk > 0.9:
            return True
