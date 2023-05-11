# overview.md

See above markdown file for current progress and a more detailed project breakdown

The following program is a sample market making strategy using the driftpy examples repo as its starting point. 

It's since been extended towards being more modular and being able to implement progressively more complex strategies through one framework. This interacts with the Javascript SDK as well.
This program interacts with drift protocol-v2 using python sdk

dependencies: [driftpy](https://drift-labs.github.io/driftpy/)

## Quick Setup

creates a virtualenv called "venv"

```
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
## Quick Run

It is assumed ANCHOR_WALLET=path/to/id.json already configured.
If not, find your private key and place it in a .env file in the root directory.

Running the following command and you will be prompted to choose between running from different strategies in src/strategies. You will be prompted to select a number but any key diverts to default, the only implemented (for now)
```
python src/main.py
```

As there's still bugs and its not fully operational, the POST error (as shown below) can be better analyzed with the default scripts, my modified one that requires no additional terminal prompts and the original.

```python
The error statement "Could not find spot market 0 at .." loads from
programs/drift/src/state/spot_market_map.rs:35, where it should instead come from SpotMarketNotFound
programs/drift/src/state/perp_market_map.rs:70 -> return Error(ErrorCode::SpotMarketNotFound);
found at
programs/drift/src/math/margin.rs:554
Run:
```
python floating_maker_simplified.py
```
or:
```
python floating_maker.py --amount .1 --market SOL-PERP
```

post two maker orders for SOL/USDC on mainnet with subaccount_id = 2

```
python floating_maker.py --amount .69 --market SOL --env mainnet --subaccount 2
```

stake 1 USDC (market_index=0) to drift v2 insurance fund (on devnet, also default)
```
python if_stake.py --operation add --amount 1 --market 0 --env devnet
```

## Disclaimer

This is experimental software is for educational purposes only on a developer testnet. USE THIS OPEN SOURCE SOFTWARE AT YOUR OWN RISK. THE AUTHORS AND ALL AFFILIATES ASSUME NO RESPONSIBILITY FOR YOUR RESULTS.
