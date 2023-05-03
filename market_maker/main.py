import os
import json
import copy
import re

from anchorpy import Wallet
from anchorpy import Provider
from solana.keypair import Keypair
from solana.rpc.async_api import AsyncClient

from driftpy.constants.config import configs
from driftpy.types import *
#MarketType, OrderType, OrderParams, PositionDirection, OrderTriggerCondition

from driftpy.clearing_house import ClearingHouse
from driftpy.clearing_house_user import ClearingHouseUser
from driftpy.constants.numeric_constants import BASE_PRECISION, PRICE_PRECISION, QUOTE_PRECISION, PEG_PRECISION
from borsh_construct.enum import _rust_enum

from driftpy.clearing_house_user import ClearingHouseUser
from driftpy.addresses import *
from driftpy.accounts import *
import extractkey
import drift_api.market_data
import drift_api.orders
import drift_api.positions
import strategy

from dotenv import load_dotenv
load_dotenv()

@_rust_enum
class PostOnlyParams:
    NONE = constructor()
    TRY_POST_ONLY = constructor()
    MUST_POST_ONLY = constructor()

def configure_drift():
    keypath = os.environ.get('ANCHOR_WALLET')
    env = 'devnet'
    url = 'https://api.devnet.solana.com'
    market_name = "SOL-PERP"

    with open(os.path.expanduser(keypath), 'r') as f: secret = json.load(f) 
    #Check if private key is base64 or base58. Extract key accordingly
    base58check = re.compile('[g-zG-Z]')
    is_base58 = base58check.search(secret['secretKey'])
    
    #Base58 calls helper function to convert to Base64. Else handle accordingly 
    if is_base58: kp = Keypair.from_secret_key(extractkey.get_base64_key(secret['secretKey']))
    else: kp = Keypair.from_secret_key(bytes(secret))

    #Default configs

    config = configs[env]
    wallet = Wallet(kp)
    connection = AsyncClient(url)
    provider = Provider(connection, wallet)
    drift_acct = ClearingHouse.from_config(config, provider)
    
    default_order = drift_api.orders.MMOrder().orderparams    
    chu = ClearingHouseUser(drift_acct, drift_acct.authority)
    user = await drift_acct.get_user()
    perp_market = await get_perp_market_account(ch.program, default_order.market_index)
    return drift_acct, chu, user, perp_market

async def main():
    """
    Entry point of the script. This function sets up the necessary objects and configuration and begins the market-making
    logic.
    """
    drift_acct, chu, user, perp_market = configure_drift()
    amm = perp_market.amm

    # Initialize the strategy object with the necessary parameters
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

    # Run the market-making loop
    while True:
        try:
            # Get the current market data
            """
            market_data = MarketData(
                bid_price=clearing_house.get_best_bid_price('SOL-PERP'),
                ask_price=clearing_house.get_best_ask_price('SOL-PERP'),
                last_trade_price=clearing_house.get_last_trade_price('SOL-PERP'),
                order_book=clearing_house.get_order_book('SOL-PERP', strategy.order_book_levels),
                recent_trades=clearing_house.get_recent_trades('SOL-PERP')
            )
            """

            # Update the strategy with the new market data
            strategy.update(market_data)

            # Calculate the desired position size based on the updated strategy
            desired_position_size = strategy.calculate_desired_position_size()

            # Get the current positions and inventory from the clearing house
            positions = clearing_house.get_positions()

            # Apply the risk management logic to adjust the desired position size
            risk_adjusted_position_size = strategy.apply_risk_management(desired_position_size, positions, inventory)

            # Place orders based on the new position size and updated market data
            orders = strategy.place_orders(risk_adjusted_position_size, market_data)

            # Submit the orders to the clearing house
            for order in orders:
                clearing_house.submit_order(order)

            # Wait for the next loop iteration
            time.sleep(10)

        except Exception as e:
            print(f"Exception in market-making loop: {e}")
            time.sleep(10)

if __name__ == '__main__':
    asyncio.run(main())

