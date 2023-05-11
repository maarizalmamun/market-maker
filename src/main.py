import os
import json
import copy
import re
import asyncio
import time
#import TA-Lib

from anchorpy import Wallet
from anchorpy import Provider
from solana.keypair import Keypair
from solana.rpc.async_api import AsyncClient

from driftpy.constants.config import configs
from driftpy.types import *
from driftpy.clearing_house import ClearingHouse
from driftpy.clearing_house_user import ClearingHouseUser
from driftpy.constants.numeric_constants import BASE_PRECISION, PRICE_PRECISION, QUOTE_PRECISION, PEG_PRECISION
from borsh_construct.enum import _rust_enum

from driftpy.addresses import *
from driftpy.accounts import *
from graph_trade import generate_graph

from driftclient import DriftClient, MMOrder, Orders
from utils import *
import importlib

from strategies import *

#from orders import MMOrder, Orders
from strategies.mean_reversion import MeanReversion
from src import *
from typing import Tuple

@_rust_enum
class PostOnlyParams:
    NONE = constructor()
    TRY_POST_ONLY = constructor()
    MUST_POST_ONLY = constructor()

async def main(keypath, consolePrint):
    """Drift Market Maker program that collects market data, 
    executes a trading strategy, and posts orders to the exchange.

    Program Flow:
    1. Initialize connection
    2. Market Making Loop begins:
        a) Data Collection, formatting, Storage, Waiting
            i) Javascript execution for DLOB retrieval
            ii) DriftPy for Perpetual Market Data
            iii) asyncio.sleep
            iv) Store/Remove Sample Data
        b) Execute loaded MM Strategy
            i) Oversized position check
            ii) Undersized position check
            iii) Determine new orders
            iv) Post transactions
        c) Post Transactions
        d) Loop to 2a)
    3. Exit call
    """
    #1 Initialize connection
    driftclient = DriftClient(keypath)
    on = True
    buffer = 0
    storage_maxed = False
    total_collateral = []
    storage = (buffer, storage_maxed, total_collateral)
    # Display initialized accounts on Solana devnet
    user_acc_key = driftclient.get_accounts(True,consolePrint)['user_account'].__str__()
    # Initialize Market Maker Algorithm
    strategyClass = choose_strategy()
    #2 Market Maker Loop Begins
    while on:

        # Fetch, Format, Collect Data
        dlob_data, user_data, market_data = await collect_and_format_data(driftclient, consolePrint)
        # Handle data archiving and Graph Generation
        storage = handle_archives(dlob_data, user_data, market_data, storage)
        # Load Fetched data to Strategy algorithm
        strategy = strategyClass(dlob_data,user_data,market_data,
            driftclient.drift_acct,driftclient.drift_acct.get_user_account_public_key())
        # Calculate order and execute trade according to strategy
        await make_trade(strategy)

        if DEV_MODE or not on:
            break
    print("Program Completes!")

async def make_trade(strategy):
    """Execute a trade using the specified strategy.

    Args:
        strategy: The strategy object to use for trading.

    """
    marketMakerOrders = strategy.post_orders()
    if marketMakerOrders != None:
        print(marketMakerOrders.order_print())
        await marketMakerOrders.send_orders()
    else:
        print("No new trades to be made.")


async def collect_and_format_data(driftclient: DriftClient, consolePrint: bool, trade_freq: int = TRADE_FREQUENCY):
    """ Fetches DLOB, User, and market data dictionaries from 
        Driftpy and Drift Javascript SDK. Data formatted and prepared for trading
        operations. Batches asyncronous retrieval times with trade_freq to 
        optimize wait time and increase possible trading frequency

    Args:
        driftclient (DriftClient): An instance of the DriftClient class, which provides a high-level interface to interact
    Returns:
        Three dictionaries:
            - dlob_data (dict): The Decentralized-Limit Order Book dictionary.
            - user_data (dict): The user account data.
            - market_data (dict): The market data.
    """
    # Fetch Data
    if DEV_MODE: 
        dlob_data, user_data, market_data = read_archived_dataset()
    if not DEV_MODE: 
        dlob_data, user_data, market_data = await fetch(driftclient)
    
    # Format Data
    dlob_data, user_data, market_data = format(dlob_data, user_data, market_data)

    # Print Data to console
    if (consolePrint):
        print_all_data(dlob_data, user_data, market_data)
    return (dlob_data, user_data, market_data)

async def fetch(driftclient: DriftClient, trade_freq: int = TRADE_FREQUENCY):
    """ 
    Fetches Decentralized-Limit Order Book (DLOB), user, and market data dictionaries from Driftpy and the Drift Javascript SDK. Data is formatted and prepared for trading operations. Asyncronous retrieval times are batched with trade_freq to optimize wait time and increase possible trading frequency.

    
    Args:
        driftclient (DriftClient): An instance of the DriftClient class, which provides a high-level interface to interact
            with the Drift Protocol.

    Returns:
        Three dictionaries:
            - dlob_data (dict): The Decentralized-Limit Order Book data.
            - user_data (dict): The user account data.
            - market_data (dict): The market data.
    """
    # Fetch from driftpy
    coroutines = [driftclient.fetch_chu_data(), asyncio.sleep(trade_freq)]
    data = await asyncio.gather(*coroutines)
    user_data, market_data = data[0]
    # Fetch from Javascript SDK
    dlob_data = fetch_javascript_json('dlob')
    return (dlob_data, user_data, market_data)

def format(dlob_data: dict, user_data: dict, market_data: dict):
    """
    Fetches DLOB, user, and market data.
    
    Args:
        driftclient (DriftClient): An instance of the DriftClient class, which provides a high-level interface to interact
            with the Drift Protocol.
        t_fq (float): The trade frequency in seconds.

    Returns:
        Three dictionaries:
            - dlob_data (dict): The Decentralized-Limit Order Book data.
            - user_data (dict): The user account data.
            - market_data (dict): The market data.
    """
    dlob_data = format_dlob(dlob_data)
    user_data, market_data = make_data_readable([user_data, market_data])
    return (dlob_data, user_data, market_data)

def handle_archives(dlob_data, user_data, market_data, storage, storage_frequency: int = COLLECTION_FREQUENCY) -> None:
    """Archives dataset containing DLOB, user and market data. The function will check if the
    number of files has exceeded the maximum limit (storage_maxed) or if it is time to archive 
    based on the frequency of the trades. Once the number of files has exceeded the maximum limit, 
    the oldest file in the queue will be deleted. The archive event is triggered every 
    storage_frequency * TRADING_FREQUENCY seconds. If the buffer is not at maximum capacity, the 
    program will add the total collateral data point to the total_collateral list. The dataset will 
    be appended to the existing archive. If the buffer is at maximum capacity, data will be 
    overwritten in a first in, first out manner. 
    """
    buffer, storage_maxed, total_collateral = storage

    # Oldest archive deleted
    delete_oldest_archived(buffer, storage_maxed)
    # Archive
    if DEV_MODE:
        return
    else:
        print(f"TradeCount: {buffer+1}, Data Storage Maxed: {storage_maxed}")
        if buffer % COLLECTION_FREQUENCY ==0:
            archive_dataset([dlob_data,user_data,market_data])
            generate_graph()
        buffer = (buffer+1) % STORAGE_BUFFER
        if buffer == 0 and not storage_maxed: 
                total_collateral.append(user_data['total_collateral'])
        elif buffer == 0: 
            storage_maxed = True
    return (buffer, storage_maxed, total_collateral)

if __name__ == '__main__':
    import argparse
    from dotenv import load_dotenv
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument('--keypath', type=str, required=False, default=os.environ.get('ANCHOR_WALLET'))
    parser.add_argument('--console', type=str, required=False, default="yes")
    args = parser.parse_args()

    if args.keypath is None:
        if os.environ.get['ANCHOR_WALLET'] is None:
            raise NotImplementedError("need to provide keypath or set ANCHOR_WALLET")
        else:
            args.keypath = os.environ.get['ANCHOR_WALLET']

    consolePrint = args.console.lower()
    if 'n' in args.console.lower() or 'f' in args.console.lower():
        consolePrint = False
    else:
        consolePrint = True

    asyncio.run(main(args.keypath, consolePrint))