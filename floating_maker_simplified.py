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
from driftpy.constants.numeric_constants import BASE_PRECISION,PRICE_PRECISION,QUOTE_PRECISION,PEG_PRECISION
from borsh_construct.enum import _rust_enum

from driftpy.addresses import *
from driftpy.accounts import *

from src.utils import extractKey
from dotenv import load_dotenv
load_dotenv()

@_rust_enum
class PostOnlyParams:
    NONE = constructor()
    TRY_POST_ONLY = constructor()
    MUST_POST_ONLY = constructor()

async def main():

    keypath = os.environ.get('ANCHOR_WALLET')
    env = 'devnet'
    url = 'https://api.devnet.solana.com'
    market_name = "SOL-PERP"
    base_asset_amount = float(0.1)
    subaccount_id = int(0)
    spread = float(0.01)
    offset = float(0)

    with open(os.path.expanduser(keypath), 'r') as f: secret = json.load(f) 
    #Check if private key is base64 or base58. Extract key accordingly
    base58check = re.compile('[g-zG-Z]')
    is_base58 = base58check.search(secret['secretKey'])
    
    #Base58 calls helper function to convert to Base64. Else handle accordingly 
    #if is_base58: kp = Keypair.from_secret_key(extractkey.get_base64_key(secret['secretKey']))
    if is_base58: kp = Keypair.from_secret_key(extractKey(secret['secretKey']))
    else: kp = Keypair.from_secret_key(bytes(secret))

    #Default configs
    config = configs[env]
    wallet = Wallet(kp)
    connection = AsyncClient(url)
    provider = Provider(connection, wallet)
    drift_acct = ClearingHouse.from_config(config, provider)

    is_perp  = 'PERP' in market_name.upper()
    market_type = MarketType.PERP() if is_perp else MarketType.SPOT()

    market_index = -1
    for perp_market_config in config.markets:
        if perp_market_config.symbol == market_name:
            market_index = perp_market_config.market_index
    for spot_market_config in config.banks:
        if spot_market_config.symbol == market_name:
            market_index = spot_market_config.bank_index

    default_order_params = OrderParams(
                order_type=OrderType.LIMIT(),
                market_type=market_type,
                direction=PositionDirection.LONG(),
                user_order_id=0,
                base_asset_amount=int(base_asset_amount * BASE_PRECISION),
                price=0,
                market_index=market_index,
                reduce_only=False,
                post_only=PostOnlyParams.TRY_POST_ONLY(),
                immediate_or_cancel=False,
                trigger_price=0,
                trigger_condition=OrderTriggerCondition.ABOVE(),
                oracle_price_offset=0,
                auction_duration=None,
                max_ts=None,
                auction_start_price=None,
                auction_end_price=None,
            )

    #accounts_print(drift_acct)
    print(market_index)
    await perpmarket_print(drift_acct, default_order_params)

    bid_order_params = copy.deepcopy(default_order_params)
    bid_order_params.direction = PositionDirection.LONG()
    bid_order_params.oracle_price_offset = int((offset - spread/2) * PRICE_PRECISION)
             
    ask_order_params = copy.deepcopy(default_order_params)
    ask_order_params.direction = PositionDirection.SHORT()
    ask_order_params.oracle_price_offset = int((offset + spread/2) * PRICE_PRECISION)

    order_print([bid_order_params, ask_order_params], market_name)

    perp_orders_ix = []

    if is_perp:
        print("Posting get_place_perp_order_ix")
        perp_orders_ix = [
            await drift_acct.get_place_perp_order_ix(bid_order_params, subaccount_id),
            ]

    await drift_acct.send_ixs(
        [
        await drift_acct.get_cancel_orders_ix(subaccount_id),
        ] + perp_orders_ix
    )


def order_print(orders: list[OrderParams], market_str=None):
    for order in orders:
        if order.price == 0:
            pricestr = '$ORACLE'
            if order.oracle_price_offset > 0:
                pricestr += ' + '+str(order.oracle_price_offset/1e6)
            else:
                pricestr += ' - '+str(abs(order.oracle_price_offset)/1e6)
        else:
            pricestr = '$' + str(order.price/1e6)
        print(str(order.direction).split('.')[-1].replace('()',''), market_str, '@', pricestr)

def accounts_print(ch: ClearingHouse):
    #Initialize Drift User using -> await drift_acct.intialize_user() 
    print("Printing relevant account public keys...")   
    print("Authority:     ", ch.authority)
    print("(Global) State:", ch.get_state_public_key())
    print("User Stats:    ", ch.get_user_stats_public_key())
    print("User Account:  ", ch.get_user_account_public_key())

async def driftuser_print(ch: ClearingHouse):
    user = await ch.get_user()
    user_pos = user.perp_positions
    user_status = user.is_margin_trading_enabled
    #print(user.perp_positions[0])
    #print(user.status,user.is_margin_trading_enabled)

async def perpmarket_print(ch: ClearingHouse, order_params):


    perp_market = await get_perp_market_account(ch.program, order_params.market_index)
    amm = perp_market.amm
    lastoracle, lastmark, lastbid, lastask = (
    amm.historical_oracle_data.last_oracle_price/PRICE_PRECISION,
    amm.last_mark_price_twap/PRICE_PRECISION,
    amm.last_bid_price_twap/PRICE_PRECISION,
    amm.last_ask_price_twap/PRICE_PRECISION)
    print("SOL-PERP Last Oracle Price", lastoracle, "Last Mark Price: ", lastmark ,"Last Bid Price: ", lastbid ,"Last Ask Price:", lastask)
    
    """    
    sol_res = amm.base_asset_reserve/BASE_PRECISION
    usdc_res = amm.quote_asset_reserve/QUOTE_PRECISION
    peg = amm.peg_multiplier /PEG_PRECISION
    fundingrate = amm.last_funding_rate/BASE_PRECISION * 10
    print("SOL: ", sol_res," USDC: ", usdc_res)
    print("Last funding rate: ", fundingrate)
    """

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())