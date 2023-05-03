import time
from typing import List
from driftpy.constants.config import configs
from driftpy.types import *

from driftpy.clearing_house import ClearingHouse
from driftpy.clearing_house_user import ClearingHouseUser
from driftpy.constants.numeric_constants import BASE_PRECISION,PRICE_PRECISION,QUOTE_PRECISION,PEG_PRECISION
from borsh_construct.enum import _rust_enum

from driftpy.addresses import *
from driftpy.accounts import *

@_rust_enum
class PostOnlyParams:
    NONE = constructor()
    TRY_POST_ONLY = constructor()
    MUST_POST_ONLY = constructor()

class MMOrder:
    """Represents an order that has been placed on the exchange.

    Attributes:
        order_type (str): The type of order (limit, market, etc.).
        market_name (str): The market_name for the asset being traded.
        direction (str): The direction of the order (buy or sell).
        order_size (float): The order_size of the asset being traded.
        price (float): The price at which the order is being placed.
        spread (float): 
        offset (float):
    """

    def __init__(
        self,
        order_size: float = 0.1,
        direction: PositionDirection = PositionDirection.LONG(),
        order_type: OrderType = OrderType.LIMIT(),
        market_name: str = 'SOL-PERP',
        post_only: PostOnlyParams = PostOnlyParams.TRY_POST_ONLY(),
        spread: float = 0.01,
        offset: float = 0.00

    ):
        is_perp  = 'PERP' in market_name.upper()
        market_type = MarketType.PERP() if is_perp else MarketType.SPOT()
        for perp_market_config in config.markets:
            if perp_market_config.symbol == market_name:
                market_index = perp_market_config.market_index
        for spot_market_config in config.banks:
            if spot_market_config.symbol == market_name:
                market_index = spot_market_config.bank_index

        self.orderparams = OrderParams(
            order_type,
            market_type=market_type,
            direction=direction,
            user_order_id=0,
            base_asset_amount= int(order_size* BASE_PRECISION),
            price=0,
            market_index=market_index,
            reduce_only=False,
            post_only=post_only,
            immediate_or_cancel=False,
            trigger_price=0,
            trigger_condition=OrderTriggerCondition.ABOVE(),
            oracle_price_offset=int((offset - spread/2) * PRICE_PRECISION),
            auction_duration=None,
            max_ts=None,
            auction_start_price=None,
            auction_end_price=None,
        )


class Orders:
    """Class for managing orders on the exchange.

    Attributes:
        drift_acct (ClearingHouse): The API object for interacting with the exchange.
        orders (List[MMOrder]): The list of orders currently on the exchange.
    """

    def __init__(self, drift_acct: ClearingHouse):
        self.drift_acct = drift_acct
        self.orders = []

    def place_order(
        self,
        order_size: float,
        direction: PositionDirection = PositionDirection.LONG(),
        order_type: OrderType = OrderType.LIMIT(),
        market_name: str = 'SOL-PERP',
        post_only: PostOnlyParams = PostOnlyParams.TRY_POST_ONLY(),
        spread: float = 0.01,
        offset: float = 0.00,        
    ) -> MMOrder:

        is_perp  = 'PERP' in market_name.upper()
        market_type = MarketType.PERP() if is_perp else MarketType.SPOT()
        
        for perp_market_config in config.markets:
            if perp_market_config.symbol == market_name:
                market_index = perp_market_config.market_index
        for spot_market_config in config.banks:
            if spot_market_config.symbol == market_name:
                market_index = spot_market_config.bank_index

        orderparams = OrderParams(
            order_type,
            market_type=market_type,
            direction=direction,
            user_order_id=0,
            base_asset_amount= int(order_size* BASE_PRECISION),
            price=0,
            market_index=market_index,
            reduce_only=False,
            post_only=post_only,
            immediate_or_cancel=False,
            trigger_price=0,
            trigger_condition=OrderTriggerCondition.ABOVE(),
            oracle_price_offset=int((offset - spread/2) * PRICE_PRECISION),
            auction_duration=None,
            max_ts=None,
            auction_start_price=None,
            auction_end_price=None,
        )

        if is_perp:
            order_ix = self.drift_acct.get_place_perp_order_ix(default_order_params)
            response = self.drift_acct.send_ixs([order_ix])
            order_id = response[0]
        else:
            order_id = self.drift_acct.place_order(default_order_params)

        order = MMOrder(
            order_size = order_size,
            direction = direction,
            order_type = order_type,
            market_name = market_name,
            post_only = post_only,
            spread = spread,
            offset = offset,        
        )

        self.orders.append(order)

        return order

    def order_print(orders: list[MMOrder], market_str=None):
        for mm_order in orders:
            order = mm_order.orderparams
            if order.price == 0:
                pricestr = '$ORACLE'
                if order.oracle_price_offset > 0:
                    pricestr += ' + '+str(order.oracle_price_offset/1e6)
                else:
                    pricestr += ' - '+str(abs(order.oracle_price_offset)/1e6)
            else:
                pricestr = '$' + str(order.price/1e6)

            if market_str == None:
                market_str = configs['mainnet'].markets[order.market_index].symbol

            print(str(order.direction).split('.')[-1].replace('()',''), market_str, '@', pricestr)

