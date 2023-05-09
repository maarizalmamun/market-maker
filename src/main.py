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

from driftclient import DriftClient, MMOrder, Orders
from utils import *
import importlib

from strategies import *

#from orders import MMOrder, Orders
from strategies.mean_reversion import MeanReversion
from src import *
from typing import Tuple
from dotenv import load_dotenv
load_dotenv()

@_rust_enum
class PostOnlyParams:
    NONE = constructor()
    TRY_POST_ONLY = constructor()
    MUST_POST_ONLY = constructor()

async def main():
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
    driftclient = DriftClient()
    storage_maxed = False
    condition = False
    buffer = 0
    start_position = []
    # Verify correct addresses on Solana devnet
    user_acc_key = driftclient.get_accounts(True)['user_account'].__str__()
    #2 Market Maker Begins
    while True:
        if condition:
            break

        # Fetch and Format data, and sleep as a batched task to align computational calculation time
        dlob_data, user_data, market_data = await collect_and_format_data(driftclient, storage_maxed)
        



        # Create an instance of the selected strategy class and execute it
        console_line()
        strategy_instance = choose_strategy()(dlob_data,user_data,market_data,
                driftclient.acct.get_user_account_public_key())
        print("Strategy begins!")
        # Initialized Market Maker
        strategy_instance.trade()

        marketMakerOrders = strategy_instance.trade()
        orderslist = Orders(driftclient.acct)
        for order in marketMakerOrders:
            orderslist.add_order(order)
        # Send txs
        
        await orderslist.send_orders()

        if DEV_MODE or stop:
            break



    print("Program Completes!")

    # Archive Function
    def handle_archives(storage_frequency: int = COLLECTION_FREQUENCY, 
        max_files_archived: int = STORAGE_BUFFER) -> None:
        """Archives dataset containing DLOB, user and market data. The function will check if the
        number of files has exceeded the maximum limit (storage_maxed) or if it is time to archive 
        based on the frequency of the trades. Once the number of files has exceeded the maximum limit, 
        the oldest file in the queue will be deleted. The archive event is triggered every 
        storage_frequency * TRADING_FREQUENCY seconds. If the buffer is not at maximum capacity, the 
        program will add the total collateral data point to the start_position list. The dataset will 
        be appended to the existing archive. If the buffer is at maximum capacity, data will be 
        overwritten in a first in, first out manner. 
        
        Args:
            storage_frequency (int, optional): The number of trades after which to archive data. Defaults to COLLECTION_FREQUENCY.
            max_files_archived (int, optional): The maximum number of files to archive. Defaults to STORAGE_BUFFER.

        Returns:
            None
        """
        print("Trade count: ", buffer, )
        if buffer % STORAGE_BUFFER == 0 and storage_maxed: 
            # Oldest archive deleted
            delete_oldest_archived()
        # Archive
        if not DEV: archive_dataset([dlob_data,user_data,market_data])
        buffer = (buffer+1) % STORAGE_BUFFER
        print(f"buffer = {buffer}, storage_maxed = {storage_maxed}\n")
        if buffer == 0 and not storage_maxed: 
                start_position.append(user_data['total_collateral'])
        elif buffer == 0: 
            storage_maxed = True

async def collect_and_format_data(driftclient: DriftClient, trade_freq: int = TRADE_FREQUENCY):
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
    coroutines = [driftclient.fetch_chu_data(), asyncio.sleep(t_fq)]
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

if __name__ == '__main__':
    asyncio.run(main())