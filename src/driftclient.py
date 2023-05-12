import os
import json
import copy
import re
import asyncio
from typing import Dict

from anchorpy import Wallet
from anchorpy import Provider
from solana.keypair import Keypair
from solana.publickey import PublicKey
from solana.rpc.async_api import AsyncClient

from driftpy.constants.config import configs
from driftpy.types import *
#MarketType, OrderType, OrderParams, PositionDirection, OrderTriggerCondition

from driftpy.clearing_house import ClearingHouse
from driftpy.clearing_house_user import ClearingHouseUser
from driftpy.constants.numeric_constants import BASE_PRECISION,PRICE_PRECISION, QUOTE_PRECISION,PEG_PRECISION, FUNDING_RATE_PRECISION
from driftpy.math.oracle import *
from borsh_construct.enum import _rust_enum

from driftpy.addresses import *
from driftpy.accounts import *

from utils import extractKey, console_line
import sys
from pathlib import Path
base_path = Path(__file__).resolve().parent
sys.path.append(str(base_path.parent))
from src import *

from dotenv import load_dotenv
load_dotenv()

@_rust_enum
class PostOnlyParams:
    NONE = constructor()
    TRY_POST_ONLY = constructor()
    MUST_POST_ONLY = constructor()

class DriftClient:
    """
    A class representing a client for the Drift Protocol. Handles interactions with the API.

    Attributes:
        drift_acct (ClearingHouse): An API object for interacting with the Drift Protocol.
        chu (ClearingHouseUser): An object representing a user of the Drift Protocol.
        default_order (OrderParams): The default order parameters for the client.
        orders (Orders): An object for managing orders on the exchange.
        market_index (int): The index of the market being traded.
    """

    def __init__(self, keypath: str):
        """
        Initializes a DriftClient object.
        """

        #keypath = os.environ.get('ANCHOR_WALLET')
        with open(os.path.expanduser(keypath), 'r') as f: secret = json.load(f) 
        
        # Check if private key is of type base64 or base58
        base58check = re.compile('[g-zG-Z]')
        is_base58 = base58check.search(secret['secretKey'])
        if is_base58:
            kp = Keypair.from_secret_key(extractKey(secret['secretKey']))
        else:
            kp = Keypair.from_secret_key(bytes(secret))

        #Default configs
        config = configs[ENV]
        wallet = Wallet(kp)
        connection = AsyncClient(URL)
        provider = Provider(connection, wallet)
        drift_acct = ClearingHouse.from_config(config, provider)
        self.drift_acct = drift_acct
        self.chu = ClearingHouseUser(drift_acct, use_cache=True)
        self.default_order = MMOrder().orderparams
        self.orders = Orders(self.drift_acct)
        params = get_market_parameters(MARKET_NAME)
        self.market_index = params['market_index']
        print("Initializing Drift client...")

    def get_accounts(self, return_obj: bool = False, printkeys: bool = True) -> dict:
        """
        Returns a dictionary containing public keys of relevant engaged accounts.

        Args:
            return_obj (bool): Whether to return the dictionary.
            printkeys (bool): Whether to print the dictionary.

        Returns:
            dict: A dictionary containing public keys of relevant engaged accounts.
        """        
        if printkeys:
            console_line()
            print("Engaging the following accounts in new Market Maker:")   
            print("Authority:          ", self.drift_acct.authority)
            print("Global State:       ", self.drift_acct.get_state_public_key())
            print("User Stats:         ", self.drift_acct.get_user_stats_public_key())
            print("User Account:       ", self.drift_acct.get_user_account_public_key())
            print("Perp Market Account:", get_perp_market_public_key(
                self.drift_acct.program_id, self.market_index))
            console_line()
        if return_obj:
            accountkeys = {}
            accountkeys['authority'] = self.drift_acct.authority
            accountkeys['state_account'] = self.drift_acct.get_state_public_key()
            accountkeys['user_stats_account'] = self.drift_acct.get_user_stats_public_key()
            accountkeys['user_account'] = self.drift_acct.get_user_account_public_key()
            accountkeys["perp_market"] = get_perp_market_public_key(
                self.drift_acct.program_id,self.market_index)
        return accountkeys

    async def fetch_chu_data(self):
        """Fetches all required Drift data.
        Returns:
            list[dict]: 2 dictionaries containing user data and market data.
        """        
        await self.chu.set_cache()
        # Batch asyncronous tasks (Reduce execution time)
        coroutines = [self.chu.get_total_collateral(), self.chu.get_total_perp_liability(),
        self.chu.get_unrealized_pnl(), self.chu.get_user_position(self.market_index),
        get_perp_market_account(self.chu.program, self.market_index)
        ]
        total_collateral, liability, unrealized_pnl, user_position, perp_market = await asyncio.gather(*coroutines)
        oracle_data = await get_oracle_data(self.drift_acct.program.provider.connection, perp_market.amm.oracle)
        # Extract data from fetch calls to desires format for processing
        user_data = self.extract_user_data(total_collateral, liability, unrealized_pnl, user_position)
        market_data = self.extract_market_data(perp_market, oracle_data)
        return user_data, market_data

    def extract_user_data(self, total_collateral, liability, unrealized_pnl, user_position) -> dict:
        """
        Fetches user trade data, including total collateral, perp 
        liability, unrealized profit and loss, and user position
        for the current market.
        Returns:
        dict: A dictionary containing user trade data, including:
            - 'user_position' (float): The user's current position in the market.
            - 'user_leverage' (float): The user's current leverage.
            - 'total_collateral' (float): The user's total collateral in their account.
            - 'free_collateral' (float): The user's free collateral in their account.
            - 'unrealized_pnl' (float): The user's unrealized profit or loss.
            - 'perp_liability' (float): The user's perp liability.
        """
        free_collateral = total_collateral - liability
        if total_collateral == 0: user_leverage = 0
        else: user_leverage = liability / total_collateral
        user_data = {"user_position": user_position, "user_leverage": user_leverage,
            "total_collateral": total_collateral, "free_collateral": free_collateral,
             "unrealized_pnl": unrealized_pnl, "perp_liability": liability
        }
        if user_data["user_position"] != None:
            perp_position_data =  self.extract_perp_position_data(user_data["user_position"])
            user_data["user_position"] = True
            new_user_data = {**user_data, **perp_position_data}
            return new_user_data
        else:
            return user_data

    def extract_perp_position_data(self, perp_position: PerpPosition) -> dict:
        """Returns a dictionary containing useful data from a PerpPosition object.

        Args:
            perp_position (PerpPosition): The PerpPosition object to extract data from.

        Returns:
            dict[str, any]: A dictionary containing selected data from the PerpPosition object.
                - last_cumulative_funding_rate (int): The last cumulative funding rate.
                - base_asset_amount (int): The amount of base asset.
                - quote_asset_amount (int): The amount of quote asset.
                - quote_break_even_amount (int): The break-even amount of quote asset.
                - quote_entry_amount (int): The entry amount of quote asset.
                - open_bids (int): The number of open bids.
                - open_asks (int): The number of open asks.
                - settled_pnl (int): The settled profit and loss.
                - open_orders (int): The number of open orders.
        """
        perp_position_data = {
            "last_cumulative_funding_rate": perp_position.last_cumulative_funding_rate,
            "base_asset_amount": perp_position.base_asset_amount,
            "quote_asset_amount": perp_position.quote_asset_amount,
            "quote_break_even_amount": perp_position.quote_break_even_amount,
            "quote_entry_amount": perp_position.quote_entry_amount,
            "open_bids": perp_position.open_bids,
            "open_asks": perp_position.open_asks,
            "settled_pnl": perp_position.settled_pnl,
        }
        return perp_position_data

    def extract_market_data(self, perp_market, oracle_data: OracleData = None) -> dict:
        """Returns a dictionary containing useful market data from a PerpMarket object.
        Args:
            None.
        Returns:
            Dict: A dictionary containing selected data from the PerpMarket object.
                - oracle_price (float): The current oracle price.
                - has_sufficient_number_of_datapoints (bool): Whether the oracle has sufficient datapoints to be considered reliable.
                - last_oracle_price (float): The price of the last oracle update.
                - last_oracle_price_twap (float): The time-weighted average price of the last oracle update.
                - last_mark_price_twap (float): The time-weighted average mark price.
                - last_bid_price_twap (float): The time-weighted average bid price.
                - last_ask_price_twap (float): The time-weighted average ask price.
                - last_funding_rate (float): The funding rate for the last funding interval.
                - last24h_avg_funding_rate (float): The 24-hour average funding rate.
                - volume24h (float): The trading volume over the last 24 hours.
                - oracle_std (float): The standard deviation of the oracle price.
                - mark_std (float): The standard deviation of the mark price.
                - base_spread (float): The spread between the base asset and the oracle price.
                - long_spread (float): The spread for long positions.
                - short_spread (float): The spread for short positions.
        """
        amm = perp_market.amm
        perp_data = {
            "oracle_price": oracle_data.price,
            "has_sufficient_number_of_datapoints": oracle_data.has_sufficient_number_of_datapoints,
            "last_oracle_price": amm.historical_oracle_data.last_oracle_price,
            "last_oracle_price_twap": amm.historical_oracle_data.last_oracle_price_twap,
            "last_mark_price_twap": amm.last_mark_price_twap,
            "last_bid_price_twap": amm.last_bid_price_twap,
            "last_ask_price_twap": amm.last_ask_price_twap,
            "last_funding_rate": amm.last_funding_rate,
            "last24h_avg_funding_rate": amm.last24h_avg_funding_rate,
            "volume24h": amm.volume24h,
            "oracle_std": amm.oracle_std,
            "mark_std": amm.mark_std,
            "base_spread": amm.base_spread,
            "long_spread": amm.long_spread,
            "short_spread": amm.short_spread
        }        
        return perp_data
        """
        perp_market = await get_perp_market_account(self.chu.program, self.market_index)
        amm = perp_market.amm
        oracle_data = await get_oracle_data(self.drift_acct.program.provider.connection, amm.oracle)
        
        perp_data = {
            "oracle_price": oracle_data.price,
            "has_sufficient_number_of_datapoints": oracle_data.has_sufficient_number_of_datapoints,
            "last_oracle_price": amm.historical_oracle_data.last_oracle_price,
            "last_oracle_price_twap": amm.historical_oracle_data.last_oracle_price_twap,
            "last_mark_price_twap": amm.last_mark_price_twap,
            "last_bid_price_twap": amm.last_bid_price_twap,
            "last_ask_price_twap": amm.last_ask_price_twap,
            "last_funding_rate": amm.last_funding_rate,
            "last24h_avg_funding_rate": amm.last24h_avg_funding_rate,
            "volume24h": amm.volume24h,
            "oracle_std": amm.oracle_std,
            "mark_std": amm.mark_std,
            "base_spread": amm.base_spread,
            "long_spread": amm.long_spread,
            "short_spread": amm.short_spread
        }
        """

class MMOrder:
    """Represents an order that has been placed on the exchange.

    Attributes:
        order_size (float): Number of contracts to purchase
        price (float): The price at which the order is being placed.
        order_type (str): The type of order (limit, market, etc.).
        direction (str): The direction of the order (buy or sell).
        market_name (str): The market_name for the asset being traded.
        price (float): The price at which the order is being placed.
        oracle_price_offset (float) : Purchase price offset from oracle
        spread (float): Price spread from oracle price
        offset (float): Price offset from oracle price
    """

    def __init__(
        self,
        order_size: float = 0.1,
        price: float = 0, 
        direction: PositionDirection = PositionDirection.LONG(),
        order_type: OrderType = OrderType.LIMIT(),
        market_name: str = MARKET_NAME,
        oracle_price_offset= 0,
        spread: float = 0.02, #10bps from 20
        offset: float = 0.00
    ):
        params = get_market_parameters(MARKET_NAME)
        if oracle_price_offset == 0: 
            if PositionDirection.LONG():
                oracle_offset = int((offset - spread/2) * PRICE_PRECISION)
            else:
                oracle_offset = int((offset + spread/2) * PRICE_PRECISION)

        else: oracle_offset = oracle_price_offset * PRICE_PRECISION
        self.orderparams = OrderParams(
            order_type,
            market_type=params['market_type'],
            direction=direction,
            user_order_id=0,
            base_asset_amount= int(order_size* BASE_PRECISION),
            price= int(price*PRICE_PRECISION),
            market_index=params['market_index'],
            reduce_only=False,
            post_only= PostOnlyParams.TRY_POST_ONLY(),
            immediate_or_cancel=False,
            trigger_price=0,
            trigger_condition=OrderTriggerCondition.ABOVE(),
            oracle_price_offset= oracle_offset,
            auction_duration=None,
            max_ts=None,
            auction_start_price=None,
            auction_end_price=None,
        )


class Orders:
    """Class for managing orders on the exchange.

    Attributes:
        drift_acct (ClearingHouse): The API object for interacting with the exchange.
        orders (List[MMOrder]): The list of orders to send in a transaction
    """

    def __init__(self, drift_acct: ClearingHouse, oracle_price: float=20.0):
        self.drift_acct = drift_acct
        self.orders = []
        self.oracle_price = oracle_price
        
    def add_order(self, order: MMOrder):
        self.orders.append(order)

    async def send_orders(self):
        """ Places perp orders to market from list of orders stored in Orders object"""
        orders_ix = []
        for order in self.orders:
            ix = await self.drift_acct.get_place_perp_order_ix(order.orderparams)
            orders_ix.append(ix)

        await self.drift_acct.send_ixs(
        [
        await self.drift_acct.get_cancel_orders_ix(0),
        ] + orders_ix
    )

    def order_print(self):
        """ Print orders to console  """
        print("Oracle Price: ", self.oracle_price)
        for mm_order in self.orders:
            order = mm_order.orderparams
            if order.price == 0:
                pricestr = '$ORACLE'
                if order.oracle_price_offset > 0:
                    pricestr += (' + '+str(order.oracle_price_offset/PRICE_PRECISION))
                else:
                    pricestr += (' - '+str(abs(order.oracle_price_offset)/PRICE_PRECISION))
            else:
                pricestr = '$' + str(order.price/1e6)
            print(str(order.direction).split('.')[-1].replace('()',''),
            f"{order.base_asset_amount/BASE_PRECISION:.3f}", MARKET_NAME, '@', pricestr
            )

    async def user_margin_enabled(self) -> bool:
        """ Check if margin trading enabled"""
        user = await self.drift_acct.get_user()
        return user.is_margin_trading_enabled

def get_market_parameters(market_name: str):
    """ Return market_index and market_type (perp or spot)""" 
    config = configs[ENV]
    market_index = -1
    is_perp  = 'PERP' in market_name.upper()
    market_type = MarketType.PERP() if is_perp else MarketType.SPOT()
    
    for perp_market_config in config.markets:
        if perp_market_config.symbol == market_name:
            market_index = perp_market_config.market_index
    for spot_market_config in config.banks:
        if spot_market_config.symbol == market_name:
            market_index = spot_market_config.bank_index
    return    {'market_index': market_index, 'market_type': market_type}


