import sys
from abc import ABC, abstractmethod
from typing import Any, Dict, List
from pathlib import Path
import asyncio

base_path = Path(__file__).resolve().parent
print(base_path)
sys.path.append(str(base_path.parent))
# Import the constants module from the 'src' directory
from src import *
from driftclient import Orders, MMOrder, DriftClient
from driftpy.types import *
from driftpy.constants.numeric_constants import BASE_PRECISION,PRICE_PRECISION, QUOTE_PRECISION,PEG_PRECISION, FUNDING_RATE_PRECISION

from utils import fetch_javascript_json, console_line

""" LV 1 MARKET MAKER - RISK MANAGEMENT FIXED/BINARY"""
# BASE PARAMETERS
MAX_TARGET = 100
MAX_LEVERAGE  = 2.0     
AGGRESSION  = 0.001 
MAX_ORDERS = 3
AGG_SKEW = [0.8, 1.01]
TARGET_SKEW = 0.1
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
        open_quantity_orders: Get user's long and short position sizes.
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

        self.drift_acct = drift_acct
        self.custom_signals = custom_signals
        self.strat_complexity: int = 1

        # RISK VARS
        self.levcap = MAX_LEVERAGE
        self.targetcap = MAX_TARGET#/self.oracle_price
        self.agg = AGGRESSION
        self.funding_rate = market_data['last_funding_rate']
        self.address = str(accaddress)
        self.derisk = DERISK_TARGET
        self.uprisk = UPRISK_TARGET
        self.agg_skew = AGG_SKEW
        self.target_skew = TARGET_SKEW
        self.target_skew = TARGET_SKEW
        self.max_orders = MAX_ORDERS

        # MARKET VARS
        self.oracle_price = market_data['oracle_price']
        self.best_bid = dlob_data['best_bid']
        self.best_ask = dlob_data['best_ask']
        try:
            self.mark_price = (dlob_data['best_bid'] + dlob_data['best_ask'])/2
        except:
            self.mark_price = market_data['oracle_price']
        self.long_orders = dlob_data['long_orders']
        self.short_orders = dlob_data['short_orders']

        # USER VARS
        self.active_position = user_data['user_position']
        self.current_leverage = user_data['user_leverage']
        self.total_collateral = user_data['total_collateral']
        self.unrealized_pnl = user_data['unrealized_pnl']

        if user_data['user_position']:
            self.user_position = user_data['base_asset_amount']
            self.liability = user_data["perp_liability"]
            self.risk = self.calculate_risk()
            self.open_bids_sum = user_data['open_bids']
            self.open_asks_sum = user_data['open_asks']
            self.open_bids, self.open_asks = self.open_quantity_orders()
            self.realized_pnl = user_data['settled_pnl']
        else:
            print("No position yet. Time to enter the market!")
            self.user_position = 0
            self.risk = 0
            self.liability = 0
            self.open_bids = 0
            self.open_asks = 0
            self.open_bids_sum = 0
            self.open_asks_sum = 0
            self.realized_pnl = 0

    def __str__(self) -> str:
        """
        Return a formatted string representation of the object's attributes.

        Returns:
            str: A string representation of the object's attributes.
        """
        return(
            f"{console_line(False)}\n"
            f"Strategy Parameters:\n"
            f"Custom Signals:              {self.custom_signals}\n"
            f"Strategy Complexity:         {self.strat_complexity}\n"
            f"Max Leverage:                {self.levcap}\n"
            f"Max Target Size:             {self.targetcap} USD\n"
            f"Aggression:                  {self.agg*100:.2f} %\n"
            f"Funding Rate:                {self.funding_rate*100:.2f} %\n"
            f"Derisk Factor:               {self.derisk}\n"
            f"Uprisk Factor:               {self.uprisk}\n"
            f"Aggression Skew Factor:      {self.agg_skew}\n"
            f"Max Orders:                  {self.max_orders} (Per Side)\n"
            f"{console_line(False)}\n"
            f"User Trade Data:\n"
            f"User Account Public Address: {self.address}\n"
            f"Active Position?             {self.active_position}\n"
            f"Position Size:               {self.user_position} SOL\n"
            f"Current Leverage:            {self.current_leverage:.2f}\n"
            f"Total Position Liability:    {self.liability:.2f} USD\n"
            f"Risk:                        {self.risk*100:.2f} %\n"
            f"Unrealized P&L:              {self.unrealized_pnl:.2f} USD\n"
            f"Realized P&L:                {self.realized_pnl:.2f} USD\n"
            f"Open Bids:                   {self.open_bids}\n"
            f"Open Asks:                   {self.open_asks}\n"
            f"Open Bids Total Size:        {self.open_bids_sum} SOL\n"
            f"Open Asks Total Size:        {self.open_asks_sum} SOL\n"
            f"Total Collateral:            {self.total_collateral:.2f} USD\n"
            f"{console_line(False)}\n"
            f"Market Conditions:\n"
            f"Oracle Price:                {self.oracle_price:.2f} USD\n"
            f"DLOB Mark Price:             {self.mark_price:.2f} USD\n"
            f"{console_line(False)}"
        )

    def open_quantity_orders(self) -> list[float]:
        """Get user's long and short open order sizes
        
        Returns:
            list[float]: Long and short open order sizes
        """
        if self.active_position == False:
            return [0,0]
        else:
            user_order_quantity = [0,0]
            for order in self.long_orders:
                if self.address == order["user"]:
                    user_order_quantity[0] += 1
            for order in self.short_orders:
                if self.address == order["user"]:
                    user_order_quantity[1] += 1
            return user_order_quantity  

    def calculate_risk(self) -> float:
        """Calculate current position's risk level based on risk management parameters
        
        Returns:
            float: Current position distance to max risk threshold ideally between [0.3,0.8], range of [0,1]
        """
        risk =  max(self.current_leverage/self.levcap, (self.liability/self.targetcap) * 0.8)      
        return risk

    def calculate_funding_adjustment(self) -> float:
        """Skew adjustment factor based on current and expected funding rates
        
        Returns:
            float: Negative indicates funding favors shorts,
                   Positive indicates funding favors longs.
                   Range: [-1,1]
                    -1 or +1 indicating clear funding bias, 
                    0.5 if funding rate is 0 but mark - oracle != 0
        """
        
        if self.funding_rate > 0 and self.oracle_price < self.mark_price:
            return -1.0
        elif self.funding_rate < 0 and self.oracle_price > self.mark_price:
            return 1.0
        elif self.oracle_price < self.mark_price:
            return -0.5
        elif self.oracle_price > self.mark_price:
            return 0.5
        else:
            return 0.0

    def calculate_skew_factor(self) -> float:
        """Calculates order placement skew, where positive skews to long order and vice versa
        
        Returns:
            float: Skew value for order placement
                   Value Range: between -0.75 to 0.75.
                   funding adjustment adds upto +/- 0.25
                   risk adjustment adds upto +/- 0.5
        """
        skew = float(self.calculate_funding_adjustment()) * 0.1
        if self.risk > self.uprisk:
            # Risk adjustment
            if self.user_position > 0:
                skew -= 0.5
            else:
                skew += 0.5
        return skew

    def calculate_aggression_factor(self) -> list[float]:
        """Calculate aggression based on funding rates and current position risk
        
        Returns:
            list[float]: Aggression factors for bid and ask orders.
        """
        funding = self.funding_rate
        aggression_factor = [self.agg, self.agg]
        # Normal conditions: Risk under Uprisk Factor
        if (self.risk < self.uprisk):
            # Favour shorts: tighten longs loosen shorts
            if funding > 0:
                aggression_factor = ([self.agg * self.agg_skew[0] * (1 - funding),
                    self.agg * self.agg_skew[1] * (1 + funding)]
                )
            # Favour longs: loosen longs tighten shorts
            elif funding < 0:
                aggression_factor = ([self.agg * self.agg_skew[1] * (1 - funding), 
                    self.agg * self.agg_skew[0] * (1 + funding)]
                )
            else:
                return aggression_factor

        # Risk above Risk Factor Threshold: Loosen aggression on side of risk (Increase aggression by 1.8-2.0x)
        else:
            if self.user_position > 0:
                aggression_factor = [self.agg * (1.0 + self.risk)*2, self.agg]
            else:
                aggression_factor = [self.agg, self.agg * (1.0 + self.risk)*2]
        return aggression_factor   

    def calculate_ordersize(self) -> list[float,float]:
        """Calculate bid and ask order sizes factoring in skew
        and converting Target size in USD to asset size
        
        Returns:
            list[float, float]: Sizes for long and short orders.
        """
        if self.active_position == False:
            return [self.targetcap, self.targetcap]

        # Convert target cap from USD to asset quantity
        target_cap_asset = float(self.targetcap)/self.oracle_price        
        skew = self.calculate_skew_factor() 

        base_target_long = (target_cap_asset - self.open_bids_sum -
            self.user_position)*(1.0 + skew * self.target_skew)
        base_target_short = (target_cap_asset + self.open_asks_sum + 
            self.user_position)*(1.0 - skew * self.target_skew)
        return [base_target_long, base_target_short]

    def calculate_order_params(self, bids: int = 0, asks: int = 0) -> list[list[float]]:
        """Calculate order sizes, quantity and offset.
            Spacing between the orders and sizes use quadratic spacing.
        
        Returns:
            list[list[float]]: Order sizes and offsets for bid and ask orders.
        """        
        bid_agg, ask_agg = self.calculate_aggression_factor()
        bidnum = max(bids,self.max_orders - self.open_bids)
        asknum = max(asks,self.max_orders - self.open_asks)
        bid_sizes = []
        ask_sizes = []
        bid_offsets = []
        ask_offsets = []
        
        # Configure quadratic spacing
        bid_divider = 1
        ask_divider = 1
        counter = 1
        base_target_long, base_target_short = self.calculate_ordersize()
        denominator = 0
        for i in range(1, bidnum+1):
            denominator += i        
        while counter <= bidnum:
            bid_sizes.append(counter/denominator)
            bid_offsets.append((bid_agg*(counter/denominator))*self.oracle_price)
            counter += 1
        counter = 1
        for i in range(1, asknum+1):
            denominator += i 
        while counter <= asknum:
            ask_sizes.append(counter/denominator)
            ask_offsets.append((ask_agg*(counter/denominator))*self.oracle_price)
            counter += 1

        for b in range(bidnum):
            bid_sizes[b] = base_target_long * bid_sizes[b]
        for a in range(asknum):
            ask_sizes[a] = base_target_short * ask_sizes[a]
        return[[bid_sizes,bid_offsets],[ask_sizes,ask_offsets]]  

    async def post_orders(self) -> Orders:    
        """Post orders on the market. Returns a list of orders.
        
        Returns:
            Orders: An instance of the Orders class representing the orders to be placed.
        """        
        buy_order_params, sell_order_params = self.calculate_order_params()
        orders = Orders(self.drift_acct, self.oracle_price)

        # Handle accidental case where max orders made:
        if self.open_bids > self.max_orders or self.open_asks > self.max_orders:
            await self.drift_acct.cancel_orders(0)
            await asyncio.sleep(1)
            buy_order_params, sell_order_params = self.calculate_order_params()

        # Max orders opened both sides
        elif self.open_bids == self.max_orders and self.open_asks == self.max_orders:
            return None

        # Handle trapped position by tightening aggression of opposite side
        elif len(buy_order_params[0]) == 0 or len(sell_order_params[0]) == 0:
            """
            if self.open_asks == 0:
                if self.user_position > 0:
                    await self.drift_acct.cancel_orders(0)
                    await asyncio.sleep(1)                   
                    buy_order_params, sell_order_params = self.calculate_order_params()              
                else:
                    pass

            elif self.open_bids == 0:
                if self.user_position < 0:
                    await self.drift_acct.cancel_orders(0)
                    await asyncio.sleep(1)                   
                    buy_order_params, _ = self.calculate_order_params()              
                else:
                    pass
            """
            ix = await self.drift_acct.get_cancel_orders_ix()
            orders.ixs.append(ix)
            #Cancel and recalculate positions
            buy_order_params, sell_order_params = self.calculate_order_params(3,3)

        print(f"Number of long Orders: = {len(buy_order_params[0])},Number of Short Orders: = {len(sell_order_params[0])}")
        """Order class initialized with instance of ClearingHouse"""
        for i in range(len(buy_order_params[0])):
            base_amt = buy_order_params[0][i]
            offset = buy_order_params[1][i]
            if base_amt < 0.1:
                base_amt = 0.1
                offset = buy_order_params[1][i]
                continue
            order = MMOrder(direction=PositionDirection.LONG(),
            order_size=base_amt, oracle_price_offset = -offset
            )
            orders.add_order(order)
        for i in range(len(sell_order_params[0])):
            base_amt = sell_order_params[0][i]
            offset = sell_order_params[1][i]
            if base_amt < 0.1:
                base_amt = 0.1
                offset = sell_order_params[1][i]
            order = MMOrder(direction=PositionDirection.SHORT(),
            order_size=base_amt, oracle_price_offset = offset
            )
            orders.add_order(order)
        return orders
        
    async def emergency_market_order_condition(self) -> bool:
        """Check if an emergency market order condition is met.
        
        Returns:
            bool: True if the condition is met, False otherwise.
        """
        if self.risk > 0.98:
            coroutines = [self.drift_acct.cancel_orders(), self.drift_acct.close_position(0)]
            await asyncio.gather(*coroutines)
            print("Risk threshold exceeded: Forcing market exit")
            return True
        else:
            return False

    async def force_close_positions(self) -> True:
        """Force market close of current position, cancel orders
        
        Returns:
            bool: True if the condition is met, False otherwise.
        """
        coroutines = [self.drift_acct.cancel_orders(), self.drift_acct.close_position(0)]
        print("User requested to end program: Forcing market exit")
        await asyncio.gather(*coroutines)
        return True
