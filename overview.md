   ```
   Summary:   
      - 1 Codebase
      	1.1 High-level Structure
		1.2 Codebase Overview
      - 2 Current Stages
      	2.1 Current Roadblock
		2.2 Current Progress
		2.3 Errors Resolved
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
|   |-- __init__.py
|   |-- archives.py
|   |-- dlob.py
|   |-- market.py
|   |-- user.py
|-- js_src/
|   |-- handle_dlob.js
|-- src/
|   |-- __init__.py
|   |-- constants.py
|   |-- driftclient.py
|   |-- main.py
|   |-- orders.py
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


1. src/main.py: contains the main market-making loop that connects all the pieces of the program.
2. src/driftclient.py: Provides a class for handling all API calls and SDK interfacing.
3. src/utils.py: contains utility functions for processing data and     executing javascript.
4. src/__init__.py: contains market-making constants like tick sizes, fee rates, and order sizes.
5. js_src/handle_dlob.js: a JavaScript file that handles updating the DOM via Protocol V2 Javascript SDK
6. src/strategies/base_strategy.py: defines an abstract class that serves as the interface for implementing market-making strategies. (Unpolished due to bug fixes)
7. src/strategies/default_strategy.py: implements a simple market-making strategy based on static parameters (implemented but with floating point related bugs (should've stuck to big numbers) )
8. src/strategies/mean_reversion.py: implements a market-making strategy based on mean reversion. (proof of concept to demonstrate the modularity of this project)

## 2 Current Stages

After the beginning stages of this project with modularity in mind the goal was to build not just solid the provided MM strategy, but to make the program modular end to end on both sides of the software interaction (Algorithmic Trading - Inputting/Adjusting Risk Parameters, more fluid decision making, extendability feedback and iteration with data. And on the other end determining a relatively plug and play approach to interacting with other trade pairs, markets, and exchanges). I think this did a reasonable job given personal time constraints.
2. Interactions with driftpy SDK (Reading and writing too, although due to trading activity wasn't conducted, but nontheless is end too end functional at this point).
3. Interacting and receiving information from the Javascript SDK for Protocol v2.
4. A sound framework I definitely see myself continuing to scale especially on the MM side. The framework for creating more dynamic strategies has been implemented (past the bug fixes) and outlined in src/strategies/__init__.py.
5. Identified a bug in the rust SDK that prevented placing orders on the PERP market through the SDK. (See below for snippet)
6. A framework for adding multiple layers of complexity to market making strategy or just using static parameters. The entryway to the project, in main.py, requests you to choose from any scripts in /src/strategies to implement their unique MM algorithm. Only one is initiated as of now (goal was to deliver 2-3) but the plug and play ability is ~80% there

#### Update on Bug
Issue identified at programs/drift/src/math/margin.rs:554
with wrong object is being passed: spot_market_map instead of perp_market_map.
```rust
let quote_spot_market = spot_market_map.get_ref(&market.quote_spot_market_index)?;
//This would be modified to
let quote_perp_market = perp_market_map.get_ref(&market.quote_spot_market_index)?;
```
The error statement "Could not find spot market 0 at .." loads from
programs/drift/src/state/spot_market_map.rs:35, where it should instead come from
programs/drift/src/state/perp_market_map.rs:70 -> return Err(ErrorCode::SpotMarketNotFound);
programs/drift/src/math/margin.rs:554
Although I didn't initiate in trading just yet, I didn't see it as a roadblock seeing the trading capability was there. I wanted to prioritize showcasing a robust solution to the market making challenge. Also after building out the framework a bit more (with Mean Reversion MM Strategy implemented) that I was planning to try to launch the Rust code to plug into the exchange directly through the native code.

Also its likely you guys are aware but I thought I'd push to github anyways. Can't wait to further discuss this project!
