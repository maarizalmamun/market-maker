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
|-- drift_api/
|   |-- market_data.py
|   |-- orders.py
|-- main.py
|-- strategy.py
venv/
| --...
.env
floating_maker.py
floating_maker_simplified.py
extractkey.py
```

### 1.2 Codebase Overview
Overall description of how the files work together:

The main.py file integrates various components of the project, implementing the core logic for the market-making bot. It fetches market data (DLOB, volatility, liquidity, order depth), submits orders, manages/tracks inventory and positions, and handles market making strategy (algorithm + risk management). The other Python files are organized into packages and contain classes with multiple functions inside them.

**`floater_maker.py`**
> Original code provided. Very slight modifications to cater to personal requirements (base58 private key, posting only 1 maker order)
**`floater_maker_simplified.py`**
> Modified version of floater_maker.py for simplified interaction with Drift SDK and ClearingHouse. Currently working on this to get get_place_perp_order_ix working.
**`extractkey.py`**
> Helper functions in order to successfully load a base58 private key (default of Phantom Wallet) into a solana Keypair object
**`main.py`**
> Integrates the various components of the project, implementing the core logic for the market-making bot.

**`drift_api` package**
   > **`market_data.py`**: Class with functions to track market data, such as volatility, liquidity, and order book depth. Also has functions to fetch DLOB and interact with the DLOB.
   > ```
   > get_market_data()
   > get_dlob_data()
   > ```
   > **`orders.py`**: Class with functions to manage order submission, tracking, and updating.
   > ```
   > place_order()
   > get_orders()
   > ```
   
**`strategy.py`**
> Class with the main functions for the trading strategy and risk management.
Implements logic to decide on bid/ask prices and order sizes.
   > ```
   > update(market_data)
   > apply_risk_management()
   > determine_bid_price()
   > determine_ask_price()
   > update_order_book()
   > calculate_desired_position_size()
   > place_orders()
 
## 2 Current Stages

Currently the file hierarchy explained above is not being utilized.
After this stage (debugging drift_acct.get_place_perp_order_ix())
Will the implementation of the rest be made.
We are currently working with floating_maker_simplified.py and 
floating_maker.py to successfully post orders.

### 2.1 Current Roadblock

Currently get_place_perp_order_ix does not work as required (SOL-PERP)
However, get_place_spot_order_ix does work (SOL)

Running get_place_spot_order_ix also yields an error, but an expected one.
Error Code: InsufficientCollateral. (Not enough deposited in user account)

However running get_place_perp_order_ix from either floating_maker.py
or floating_maker_simplified.py, we get the following error:

'Program log: Instruction: PlacePerpOrder', 'Program log: Could not find spot market 0 at programs/drift/src/math/margin.rs:554', 'Program log: AnchorError occurred. Error Code: SpotMarketNotFound. Error Number: 6087. Error Message: SpotMarketNotFound.'

It's been verified that the drift user has been created. Running the following
python statements yields the following results:

```python
    print("Authority:     ", ch.authority)
    print("(Global) State:", ch.get_state_public_key())
    print("User Stats:    ", ch.get_user_stats_public_key())
    print("User Account:  ", ch.get_user_account_public_key())
```

Printing relevant account public keys...
Authority:      5pRa8EiyfJm9Kzv1qNinQvGrofTFvgQ3xbNz2bbQBt4L
(Global) State: 5zpq7DvB6UdFFvpmBPspGPNfUGoBRRCE2HHg5u3gxcsN
User Stats:     8EfMeDjs1W2nP6549Tbs87sRRQCnTRfpJNap4K5sa9CL
User Account:   GKcuL8m7ddgA9ryjh3M3oQjS46hvU6mHtw1gozg2qAo5

perp_market = PerpMarket object and successfully stores perpetual market information. We can also execute get_user() function from ClearingHouse

```python
perp_market = await get_perp_market_account(ch.program, order_params.market_index)
user = await ch.get_user()
```

Right before invoking drift_acct.send_ixs, 
```python
print (perp_orders_ix)
```
To verify transaction details. The following is printed verifying all the public addresses are correct

[TransactionInstruction(keys=[AccountMeta(pubkey=5zpq7DvB6UdFFvpmBPspGPNfUGoBRRCE2HHg5u3gxcsN, is_signer=False, is_writable=False), AccountMeta(pubkey=GKcuL8m7ddgA9ryjh3M3oQjS46hvU6mHtw1gozg2qAo5, is_signer=False, is_writable=True), AccountMeta(pubkey=5pRa8EiyfJm9Kzv1qNinQvGrofTFvgQ3xbNz2bbQBt4L, is_signer=True, is_writable=False), AccountMeta(pubkey=J83w4HKfqxwcq3BEMMkPFSppX3gqekLyLJBexebFVkix, is_signer=False, is_writable=False), AccountMeta(pubkey=8UJgxaiQx5nTrdDgph5FiahMmzduuLTLf5WmsPegYA6W, is_signer=False, is_writable=True)], program_id=dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH, data=b'E\xa1]\xcax~L\xb9\x01\x01\x00\x00\x00\xe1\xf5\x05\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01x\xec\xff\xff\x00\x00\x00')]

Given J83w4HKfqxwcq3BEMMkPFSppX3gqekLyLJBexebFVkix is the oracle key for SOL and assuming 8UJgxaiQx5nTrdDgph5FiahMmzduuLTLf5WmsPegYA6W is the vault address for SOL on drift, all the addresses seem correct.

However it does mention SpotMarketNotFound which is strange when it should be PerpMarketNotFound that's expected. It also mentions the spot market (index) 0 being located in programs/drift/src/math/margin.rs:554 so perhaps that's the issue

### 2.2 Current Progress

- All of the logic for the basic market making strategy (as given as an example in the more clarifications section)  has been determined. 
- Code's architecture has been divided into modules for ease of flexibility and code scalability for introducing new markets and market making strategies (the goal was to plug in more sophisticated market making strategies if time allowed)
- driftpy ClearingHouse, ClearingHouseUser, Accounts, Addresses and their documentation has been thoroughly reviewed and its been determined how their functions will tie into the overall program logic
- Went through the entire whitepaper (including a minor calculation error I'd be happy to share in a later discussion) as well as all the drift related articles I could find to thoroughly grasp the architectures of drifts version 0,1 and 2
- Keypair initialized successfully as well as drift_acct
- Most get functions from the 4 core driftpy classes are functional. It is only 
get_place_perp_order_ix that's giving issues as of now

### 2.3 Errors Resolved
- imported a new library (dotenv, also updated in requirements.txt) in order to configure the os environment variable ANCHOR_WALLET from a .env folder
- successfully utilized a secret key in base58 format in order to create our solana Keypair object
    - This required a workaround. A seperate function was created in 
    extractkey.py. The function get_base64_key(base58str) takes the secretkey in base58 and returns a base64 key in the datatype bytes.
    - This was done by creating a solders Keypair which does take base58 as an input. Then using its built in function to return secret key in bytes. This is then passed to the original statement to create solana Keypair object.
- In order to post transactions to drift SDK, we needed to call the function intialize_user from ClearingHouse
    - Until then there was an address issue. It kept returning the User Account address GKcuL8m7ddgA9ryjh3M3oQjS46hvU6mHtw1gozg2qAo5 without ever having any transaction history. Initialization created the user.
