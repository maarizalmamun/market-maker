
COMPLEXITY = 1
""" LV 2 MARKET MAKER - RISK MANAGEMENT VARIABLE/ANALOG
    VIA DIRECT DATA

The framework has been built with a basic implementation example.
Adjustment factors would convert the above fixed risk management
parameters/thresholds and make them more analog. 
"""

if COMPLEXITY == 1:
    """LV 1 MARKET MAKER - RISK MANAGEMENT FIXED/BINARY"""

    MAX_TARGET = 100
    """int: The maximum target size for positions."""

    MAX_LEVERAGE = 2
    """float: The maximum leverage ratio (total position value to available collateral)."""

    AGGRESSION = 0.001
    """float: The level of aggressiveness to use when placing orders."""

    MAX_ORDERS = 3
    """int: The maximum number of orders to place at any given time."""

    # BASE DERISK/UPRISK THRESHOLDS (% OF LIMIT)
    DERISK_TARGET = 0.8
    """float: The derisk target (as a percentage of `MAX_TARGET`)."""

    DERISK_LEVERAGE = 0.8
    """float: The derisk leverage (as a percentage of `MAX_LEVERAGE`)."""

    UPRISK_TARGET = 0.3
    """float: The uprisk target (as a percentage of `MAX_TARGET`)."""

    UPRISK_LEVERAGE = 0.3
    """float: The uprisk leverage (as a percentage of `MAX_LEVERAGE`)."""
    

else:
    """
    LV 2 MARKET MAKER - RISK MANAGEMENT VARIABLE/ANALOG VIA DIRECT DATA
    The framework has been built with a basic implementation example.
    Adjustment factors would convert the above fixed risk management
    parameters/thresholds and make them more analog. 

    """

    if(COMPLEXITY) > 1:
        TARGET_ADJUST = [0.5, 2]
        """List[float]: The minimum and maximum adjustment factors for the `MAX_TARGET` parameter."""

        MAX_LEVERAGE_ADJUST = [0.5, 2]
        """List[float]: The minimum and maximum adjustment factors for the `MAX_LEVERAGE` parameter."""

        AGGRESSION_LIMIT_ADJUST = [10, 0.2]
        """List[float]: The minimum and maximum adjustment factors for the `AGGRESSION` parameter."""

        MAX_ORDERS_ADJUST = [0, 2]
        """List[int]: The minimum and maximum adjustment factors for the `MAX_ORDERS` parameter."""

        # BASE TOGGLES - Level 2 Strategy
        TARGET_ADJUST_ON: bool
        """Boolean value indicating whether the target adjustment factor is enabled."""

        LEV_LIM_ADJUST_ON: bool
        """Boolean value indicating whether the maximum leverage adjustment factor is enabled."""

        AGGRESSION_ADJUST_ON: bool
        """Boolean value indicating whether the aggressiveness adjustment factor is enabled."""

        TRADE_FREQ_ADJUST_ON: bool
        """Boolean value indicating whether the trade frequency adjustment factor is enabled."""

        FETCH_DATA_ADJUST_ON: bool
        """Boolean value indicating whether the data collection frequency adjustment factor is enabled."""

        FETCH_BUFFER_ADJUST_ON: bool
        """Boolean value indicating whether the data buffer size adjustment factor is enabled."""

        """ LV 3 MARKET MAKER - MARKET SIGNALS FROM PRICE DATA
        The framework has been built but not yet implemented.
        Adjustment factors would convert the above fixed risk management
        parameters/thresholds and make them more analog. """

        USE_MARKET_SIGNALS: bool
        """Boolean value indicating whether the market signals will be used by the market maker."""

        USE_CUSTOM_STRATEGY: bool
        """Boolean value indicating whether the custom strategy will be used by the market maker."""

        """LV 4 MARKET MAKER"""

        # Parameter Configurations. Each will have 3 modes of complexity. OFF (0), ON (1), Analog (0 < x < 1)
        """
        Risk Management:
        We will take a look at every variable we can look at and decide on appropriate configs for each
        - Target Size, Max Leverage vs Current. also vs Total collateral (Positional Risk)
        - Aggression
        - Skew on either

        """ 

        # LV 4 MARKET MAKER
        # 
        # Parameter Configurations


        USE_BOLLINGER_BANDS = False
        USE_MACD = False

        """
        Bollinger Bands

        Std (SMA + nstd * std, SMA - nstd * std)
        MACD

        EMA_x, EMA_y
        """
        BOLLINGER_BANDS_PERIOD = 20
        BOLLINGER_BANDS_STDEV = 2

        MACD_EMA_X_PERIOD = 12
        MACD_EMA_Y_PERIOD = 26

        """ AMM CONSTANTS """

        """ SIMULATION CONSTANTS """

        #Market
        SIMULATION_PRICE_MEAN = 10000
        SIMULATION_PRICE_STDEV = 100
        SIMULATION_VOLUME_MEAN = 100
        SIMULATION_VOLUME_STDEV = 10

        #Market Maker
        SIMULATION_MAKER_START_PRICE = 10000
        SIMULATION_MAKER_START_POSITION = 100
        SIMULATION_MAKER_MAX_POSITION = 1000

        #Simulation
        SIMULATION_START_DATE = "2022-01-01"
        SIMULATION_END_DATE = "2022-01-02"
        SIMULATION_TRADE_FREQUENCY = 12
        SIMULATION_BURN_IN_PERIOD = 120


        # CUSTOM PARAMETERS
        USE_MARKET_SIGNALS = False
        USE_CUSTOM_STRATEGY = False


# Parameter Configurations. Each will have 3 modes of complexity. OFF (0), ON (1), Analog (0 < x < 1)
"""
Risk Management:
We will take a look at every variable we can look at and decide on appropriate configs for 
each
- Target Size, Max Leverage vs Current. also vs Total collateral (Positional Risk)
- Aggression
- Skew on either above
- P&L
"""

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

Risk Management:
We will take a look at every variable we can look at and decide on appropriate configs for 
each
- Target Size, Max Leverage vs Current. also vs Total collateral (Positional Risk)
- Aggression
- Skew on either above
- P&L

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
