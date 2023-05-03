# overview.md

See above for more current progress and a more detailed project breakdown

The following program is a sample market making strategy using the driftpy examples repo as its starting point. 
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

Running the following command
posts one maker order of 0.1 for SOL-PERP on devnet (default) with main account. (floating_maker.py has been modified to not require any other inputs)
input from user.

```
python floating_maker_simplified.py
```

Original still runs as intended.
post two maker orders for SOL-PERP on devnet (default) with main account (default)

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
