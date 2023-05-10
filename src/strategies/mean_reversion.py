from src import * 
"""
Mean Reversion: Draws on the principle that over time markets
tend to return to their historical average.
With oracle and mark_std built in this is the simplest
custom strategy to implement.
We will use a simple approach drawing on the definition of
standard deviation. std assumes normal distribution of 
a set of data, a bellcurve. 
68% of data is assumed to lie within 1 std from the mean.
95% of data is assumed to lie within 2 std from the mean
This strategy will adjust risk management parameters in a skewed manner
to account for this.


"""
# Implement mean reversion
""" 
Args: oracle_std, oracle_price, oracle_twap


Returns: skewfactor (leverage, target_size)
"""


"""
    strategy = MarketMakerStrategy(
        base_asset='SOL',
        quote_asset='USDC',
        base_collateral = 1,
        quote_collateral = 100,
        total_collateral = chu.get_total_collateral(),
        free_collateral = chu.get_free_collateral(),
        asset_weight_discount = 0.8, #SpotMarket.initial_asset_weight
        aggression = 0.001,
        leverage_limit = 2,
        current_leverage = chu.get_leverage(),
        liq_price = chu.get_perp_liq_price(0),
        max_target_size = 100,
        max_dlob_orders=3,
        max_bid_spread= aggression * asset_weight_discount,
        max_ask_spread= aggression * 1.01,
        funding_rate = amm.last_funding_rate/BASE_PRECISION * 10,
        funding_rate_factor=0.5,
        funding_rate_limit=0.1,
    )
"""


class MeanReversion:
    def __init__(self,):
        #Initialize based on relevant strategy parameters
        pass

    def update(self):
        #Apply new market parameters to strategy
        #apply_risk_management(self)
        pass

    def apply_risk_management(self):
        """
        Applies risk management rules to determine whether to adjust the position size, and by how much.
        """
        if self.desired_position_size != self.current_position_size:
            # If desired and current position sizes are different, adjust position size
            self.update_risk_parameters()
            self.calculate_desired_position_size()
            self.adjust_position_size()

    def update_risk_parameters(self):
        """
        Updates the risk management parameters based on market data.
        """
        #self.market_data.update_market_data()
        #self.market_data.get_dlob_data()
        #self.market_data.update_volatility()
        pass

    def determine_bid_price(self):
        """
        Determines the bid price based on market data and the trading strategy.
        """
        pass

    def determine_ask_price(self):
        """
        Determines the ask price based on market data and the trading strategy.
        """
        pass

    def update_order_book(self):
        """
        Updates the order book with new orders and adjusts/cancels existing orders as necessary.
        """
        #self.orders.update_orders()
        pass
        # Check if current bid/ask prices are outside the spread of existing orders
        # ...

        # Cancel orders if necessary
        # ...

        # Submit new orders if necessary
        # ...

    def place_orders(self):
        """
        Places orders based on the current bid/ask prices and desired position size.
        """
        pass

    def calculate_desired_position_size(self):
        """
        Calculates the desired position size based on the current market data and risk management rules.
        Pseudocode
        prices = []
        factor = aggression * asset_weight_discount if side == Side.BUY else aggression * 1.01
        bid_price_1 = mark_price - mark_price * aggression * factor/4
        bid_price_2 = mark_price - mark_price * aggression * factor/2
        bid_price_3 = mark_price - mark_price * aggression * factor
        ask_price_1 = mark_price + mark_price * aggression * factor/4
        ask_price_2 = mark_price + mark_price * aggression * factor/2
        ask_price_3 = mark_price + mark_price * aggression * factor
        Add above to determine_ask_price and determine_bid_price
        prices.append(above_prices)
        
        """
        position_size = 1
        # Determine the desired position size based on risk management rules
        #Logic here


        # Calculate the position size based on the risk per trade and the current price/volatility
        #Logic here
        return position_size

"""
Strategy:
Fixed MM Strategy vs Binary Decisions vs Decision Matrix
^ in order of complexity

Basis: Implement logic for complexity, include adjustment factors to reduce parameters
Require Escape Mode to pull out of market if emergency thresholds met*

Strategy - Possible Modes (Decision Matrix)

x 0 0 TRENDING VS NON TRENDING (Binary vs Analog)
0 y 0 VOLATILE VS NOT (Binary vs Analog)
0 0 z HIGH VS LOW VOLUME (Binary vs Analog)

Mode  | Market Analysis Parameters       | Adjustment Parameters  | Strategy Goal
________________________________________________________________________
matrix| Factor1 | Factor2  | Factor3     | adj1   | adj2 | adj3   | 
1 1 1   Trending, Volatile, High Volume -> SkewUP, AggUP, TargetUP (1)
1 1 0   Trending, Volatile,  Low Volume -> SkewUP, AggUP, TargetLO (1)
1 0 1   Trending, Stable,   High Volume -> SkewUP, AggLO, TargetUP (1.5) (Unlikely)
1 0 0   Trending, Stable,    Low Volume -> SkewUP, AggLO, TargetLO (1.5)
0 1 1   Ranging,  Volatile, High Volume -> SkewLO, AggUP, TargetUP (2) (Rare)
0 1 0   Ranging,  Volatile,  Low Volume -> SkewLO, AggUP, TargetLO (2)
0 0 1   Ranging, Stable,    High Volume -> SkewLO, AggLO, TargetUP (Rare, Ideal MMenv) (2)
0 0 0   Ranging, Stable,    Low Volume  -> SkewLO, AggLO, TargetLO (Common, Ideal MMenv) (2)

Market Paramaters = Mode -> f(x) -> Strategy Goal
f(x) -> Risk Management = Adjustment Parameters -> g(x)
Interdependent factors but distinguishment required

Variables to Analyze:

Market (Raw)
-oracle
-mark
-bid/ask
-^orderbook, last, twaps, base/quotient long/short
-volume
-time

Market (derived, pulled directly from drift)
Trend -> (Mark/Oracle - TWAP)
Volatility
- funding, mark-oracle
- spreads (bid/ask, btwn bids/asks)
- mark/oracle std

Market (derived and calculated)
- MACD (EMA_x - EMA_y)

Adjustment Parameters:
Target ->       Collateral Risk: Max Target Size (Position Size), Max Leverage (Collateral ratio)
Aggression ->,  Bid/ask adjustment
SKEW -> Bid/Ask Skew (-1 to 1)

Initialize: Target 100. Aggression 10bps. target_skew 0. agg_skew = [1.2, 1.01] 

Target (Fixed or Variable)     Variable -> Initial * variation (0 to 2)
Aggression (Fixed or Variable) Variable -> Initial * variation (0.1 to 10)
Skew (Fixed or Variable)       Variable -> Initial * variation (-1 to 1) | (0.5 to 2)

Inputs to decide:
- Strategy Mode ()

Goal: 
> Maximize filled orders + Earn Funding Rate (1) -> Mark - Oracle, Fees/Rebate
> Focus on high profit orders (2)
"""


