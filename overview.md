   ```
   Overview:   
      - 1 Codebase
      	1.1 High-level Structure
		   1.2 Codebase Overview
      - 2 Implemented Algorithms
      	2.1 src/main.py Flow of Events
         2.2 BaseStrategy Algorithmic Sequence
      - 3 Bugs and Deliverables
   ```
## 1 Codebase
### 1.1 High-level structure

```lua
market_maker/
|-- data/
|   |-- archived/
|   |   |-- dlob/
|   |   |-- |-- dlob-230507-01:47.json
|   |   |-- market/
|   |   |-- |-- market-230507-01:47.json
|   |   |-- user/
|   |   |-- |-- user-230507-01:47.json
|   |   |-- ...
|   |-- dlob.json
|   |-- trading_result_graph.png
|-- js_src/
|   |-- handle_dlob.js
|-- src/
|   |-- __init__.py
|   |-- driftclient.py
|   |-- graph_trade.py
|   |-- main.py
|   |-- utils.py
|   |-- strategies/
|   |-- |-- __init__.py
|   |   |-- base_strategy.py
|   |   |-- default_strategy.py  
|   |   |-- mean_reversion.py  
|   |-- tests/
```
data/archived/: contains archived data in JSON format for the market, dlob, and user data, separated by timestamp.
data/archives.json: provides a class for loading archived data.
data/dlob.json: provides a class for handling driftpy exchange's orderbook data.
data/user.json: Dataset for storing JSON data on driftpy exchange's user data.

### Codebase Overview

1. src/main.py: contains the main market-making loop that connects all the pieces of the program.
2. src/driftclient.py: Provides a class for handling all API calls and SDK interfacing.
3. src/utils.py: contains utility functions for processing all fetched data, executing javascript and executing strategy script.
4. src/__init__.py: contains important file constants to be adjusted such as configuring devnet blockchain, tradepair, trading params, devmode etc.
5. js_src/handle_dlob.js: a JavaScript file that handles updating the DOM via Protocol V2 Javascript SDK
6. src/strategies/default_strategy.py: implements a simple market-making strategy based on static parameters (implemented)
7. src/strategies/base_strategy.py: defines an abstract class that serves as the interface for implementing market-making strategies. (Unimplemented as of now, default_strategy.py and all subsequent strategies would extend its functionality. Its to provide a framework
strategy template for all strategies to follow)
8. src/strategies/mean_reversion.py: implements a market-making strategy based on mean reversion. (proof of concept to demonstrate the modularity of this project, unimplemented as of now)
9. src/strategies/__init__.py: Implements the core features for implementing market making algorithms of various complexities. The baseline risk management parameters and trade strategy constant variables are set here and extended/modified in the actual strategy.py files.
9. src/data/dlob.json: Contains the live most recently pulled dlob data from the Javascript SDK
10. src/data/archived/: Directory contains archived data of dlob,market_data, and user_data. Archived according to trade parameters set in 
11. src.graph_trade.py: Creates a graph of current user collateral and compares to pnl from trade
                        Stored in data/ttrading_result_graph.png

## 2. Implemented Algorithms

### 2.1 src/main.py Flow of Events

1. Initialize user account with Solana private key stored in .env in main directory. 
2. Initialize connection to Driftpy: ClearingHouse is connected to via our custom DriftClient class. While loop now begins to continue posting transactions.
2. Fetch data from Driftpy and Drift Protocol-v2 Javascript SDK.
3. Process the data. Store in variable dictionaries, format the data to desired format, TypeCast variables and apply BigNum to regular float conversions.
4. This all occurs in a batched asyncronous coroutine that is paired alongside our sleep function to create a consistent pace of order output.
5.  Once this stage is complete, the user is prompted to select their strategy of choice.
6. Upon user selection the strategy is activated to begin processing our data into new orders to be placed on the exchange (as described below)
6. The orders are placed once the instructions have been received by the given Strategy class.
7. The orders are sent out and we repeat from step 2 until program termination.

### 2.2 BaseStrategy Algorithmic Sequence

1. After being fed in risk management constants (ie. Max Leverage, Target Size),
data points on the users trading account, market data and DLOB data are gathered.
2. Processing this data, we first determine 3 factors:
   - Risk Calculation, solving for risk management parameter at the highest risk threshold
   - Funding Adjustment, solving for which direction the current funding rate is to bias (skew) order sizes to slightly favour larger positions on this end as well as looser aggression
   - User position. Does the user hold a position? If so what's the current position. No position held forwards to default order placement.
3. We begin to convert these factors into two factors: Skew and Aggression adjustments.
   - Skew adjustments made towards higher bid or ask sizes depending on the above factors
   - Aggression adjustments made also depending on the above factors
4. With skew and aggression determined these are applied to calculate for the order size and offset for our transaction.
5. Once order size and offset is calculated, it is sent out back to the main function in src/main.py

### 3.1 Deliverables and Project Summary

After the beginning stages of this project with modularity in mind the goal was to build not just the provided MM strategy, but to make the program modular end to end on both sides of the software interaction (Algorithmic Trading - Inputting/Adjusting Risk Parameters, more fluid decision making, extendability feedback and iteration with data. And on the other end determining a relatively plug and play approach to interacting with other trade pairs, markets, and exchanges). The following are the deliverables at this stage
1. Interactions with driftpy SDK 
2. Interacting and receiving information from the Javascript SDK for Protocol v2.
3. A market making framework that could take in more complex strategies just through extending a default BaseStrategy abstract class. Scalability on both strategy implemention and exchange connections but especially on the MM side. The framework for creating more dynamic strategies has been implemented (past the bug fixes) and outlined in src/strategies/__init__.py.
4. Plot trading results to data/trading_result_graph.png
### 3.2 Update on Bug
Resolved at programs/drift/src/math/margin.rs:554
with wrong object is being passed: spot_market_map instead of perp_market_map.
Issue was: Insufficient Collateral required deposit

Current Error:

```lua
```
'Program dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH success', 'Program dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH invoke [1]', 'Program log: Instruction: PlacePerpOrder', 'Program log: oracle pubkey not found in oracle_map: 5SSkXsEKQepHHAewytPVwdej4epN1nxgLVM84L4KXgy7', 'Program log: AnchorError occurred. Error Code: OracleNotFound. Error Number: 6036. Error Message: OracleNotFound.'
```
```
Unsure why it occurs as the address is a valid devnet address