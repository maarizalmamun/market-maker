"""Utility functions for the project.

This module provides a collection of utility functions that are used throughout the project. These include functions for handling private keys, directory pathways, fetching and handling Javascript JSONs, archiving datasets, and formatting data.

Functions:
- extractKey(base58str: str) -> bytes: Converts a private key from base58 to bytes.
- data_dir_path() -> str: Returns the absolute path of the data directory.
- strategies_dir_path() -> str: Returns the absolute path of the strategies source directory.
- javascript_dir_path() -> str: Returns the absolute path of the JavaScript source directory.
- fetch_javascript_json(data: str) -> list[dict]: Executes javascript in terminal to collect data via JS SDK.
- read_javascript_data(data_name: str) -> list[dict]: Returns specified JSON file containing orders as a list of dictionaries.
- format_dlob(dlob: list[dict] = read_javascript_data('dlob')) -> dict: Formats dlob data for program usability.
- read_archived_dataset() -> list[dict]: Reads and returns all archived datasets (for development purposes only).
- read_archived_data(data_category: str) -> dict: Returns the latest archived dataset for a given data category.
- delete_oldest_archived() -> None: Deletes oldest file in each subdirectory of data/archived.
- delete_archived_data(data_category: str) -> None: Deletes the latest archive data file for a given data category.
- archive_dataset(dataset: list[dict]) -> None: Archives list of all datasets to respective directory.
- archive_data(data: dict) -> None: Archive dataset by creating a timestamped JSON and storing appropriate subdirectory in '/data/archived'.
- keyword_in_data(data, keywords: list[str]) -> bool: Checks if any of the given keywords exist in the data dictionary keys.
- make_data_readable(data: Union[dict, list]) -> Union[dict, list]: Converts BigNumber values to readable format. Formats data extracted from driftpy (Market and User data).
- create_order_book(sorted_orders: list[dict], order_tick_size: float = 0.05) -> dict: Creates an order book. Handles both long and short orderbooks.
- choose_strategy() -> None: Displays list of available strategies, prompts user selection to load given strategy. Pressing any key yields default strategy.
- update_prices(orders: list[dict]) -> list[dict]: Updates dlob entries for orders with price 0.
- filter_orders(orders: list[dict], filter: str='long', param: str='direction') -> list[dict]: Filter orders list by given field.
- filter_keys(orders: dict, filterslist: list[str]) -> dict: Filters a dictionary to only contain the specified keys.
- get_dir_path(dir_name: str) -> str: Returns the absolute path of the requested directory.
- print_all_data(dlob_data: list[dict], user_data: dict, market_data: dict) -> None: Formatted print of the datasets to the console.
- print_orders(dlob: list[dict], maxprints: int = 3) -> None: Formatted printing of dlob orders up to maxprints.
- print_ob(order_book: dict) -> None: Prints order book to console.
- console_line() -> None: Prints separator line in console.

Constants:
- BASE_PRECISION: The precision used for base amounts.
- PRICE_PRECISION: The precision used for prices.
- QUOTE_PRECISION: The precision used for quote amounts.
- PEG_PRECISION: The precision used for pegged orders
"""
import os
import json
import datetime, time
from copy import deepcopy

from typing import Union, Any, List, Dict
import asyncio
from subprocess import run
from solana.publickey import PublicKey
from driftpy.constants.config import configs
from driftpy.constants.numeric_constants import BASE_PRECISION, PRICE_PRECISION, QUOTE_PRECISION, PEG_PRECISION, FUNDING_RATE_PRECISION
import importlib

import sys
from pathlib import Path
base_path = Path(__file__).resolve().parent
sys.path.append(str(base_path.parent))
from src import *


# Private key handler
def extractKey(base58str) -> bytes:
    """
    Private Key: TypeConversion from (base58,string) to (base64, bytes)

    Args:
        base58str (str): The private key as a base58 encoded string.

    Returns:
        bytes: The private key as a base64 encoded bytes.
    """    
    from solders.keypair import Keypair
    kp = Keypair.from_base58_string(base58str)
    return kp.__bytes__()


# Directory Pathway Functions
def data_dir_path() -> str:
    """Returns the absolute path of the data directory"""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))

def strategies_dir_path() -> str:
    """Returns the absolute path of the strategies source directory"""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src','strategies'))

def javascript_dir_path() -> str:
    """Returns the absolute path of the JavaScript source directory"""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'js_src'))


# Fetching and handling of Javascript JSONs
def fetch_javascript_json(data: str) -> list[dict]:
    """ 
    Retrieves data using the Drift Javascript SDK. The output is 
    then parsed as a list of dictionaries.
    
    Args:
        data (str= 'dlob' or 'userorders'): The name of the data to be fetched as a string.
    
    Returns:
        list[dict]: The fetched data as a list of dictionaries. Each dictionary represents a single object
                    containing the data for the requested key.
    
    Raises:
        Exception: If there is a problem with the Javascript SDK retrieval or the data cannot be found.
    """
    path = os.path.join(javascript_dir_path(),'handle_dlob.js')
    try: result = run(["node", path], capture_output=True, text=True)
    except: raise Exception("APICallError: Problem retrieval from Javascript SDK")
    print(result.stdout)
    return read_javascript_data(data)

def read_javascript_data(data_name: str) -> list[dict]:
    """
    Return specified JSON file containing orders as list of dictionaries.

    Args:
        data_name (str): The name of the data file to be read as a string.

    Returns:
        list[dict]: The specified JSON file as a list of dictionaries.

    """  
    path = os.path.join(data_dir_path(), data_name + '.json')
    with open(path, 'r') as f: js_data = json.load(f)
    return js_data

def format_dlob(dlob: list[dict] = read_javascript_data('dlob')) -> dict:
    """
    Formats the provided dlob data in a more human-readable format

    Args:
        dlob (dict): The dlob data to format

    Returns:
        dict: A formatted version of the provided dlob data

        The returned dictionary has the following keys:

        - 'best_bid': A float representing the highest bid in the orderbook
        - 'best_ask': A float representing the lowest ask in the orderbook
        - 'long_orderbook': A dictionary representing the long orderbook, with the following keys:
            - 'price': A float representing the price of the order
            - 'quantity': A float representing the quantity of the order
            - 'cumulative_quantity': A float representing the cumulative quantity of all orders at or below the current price
        - 'short_orderbook': A dictionary representing the short orderbook, with the same keys as 'long_orderbook'
        - 'long_orders': A list of dictionaries representing the top long orders, with the following keys:
            - 'orderId': A string representing the ID of the order
            - 'direction': A string representing the direction of the order ('long' or 'short')
            - 'price': A float representing the price of the order
            - 'baseAssetAmount': A float representing the quantity of the order
            - 'oracle_price': A float representing the oracle price of the order
            - 'oraclePriceOffset': A float representing the offset from the oracle price of the order
        - 'short_orders': A list of dictionaries representing the top short orders, with the same keys as 'long_orders'

        The 'long_orderbook' and 'short_orderbook' dictionaries contain one entry for each price in the orderbook. The 'cumulative_quantity' 
        value is the sum of the 'quantity' values for all orders at or below the current price.
        The 'long_orders' and 'short_orders' lists contain the top 3 orders in each category, sorted by price.
        Each dictionary in the 'long_orders' and 'short_orders' lists has the same keys as described above for individual orders.
    """
    dlob = read_javascript_data('dlob')
    updated_dlob = update_prices(dlob)
    updated_dlob = filter_orders(dlob, "limit",'orderType')
    filtered_longs = filter_orders(updated_dlob, 'long', 'direction')
    filtered_shorts = filter_orders(updated_dlob,'short', 'direction')
    sorted_longs = sorted(filtered_longs, key=lambda x: x['price'], reverse=True)
    sorted_shorts = sorted(filtered_shorts, key=lambda x: x['price'])
    return {
        'best_bid': sorted_longs[0]['price'],
        'best_ask': sorted_shorts[0]['price'],
        'long_orderbook': create_order_book(sorted_longs, 0.1),
        'short_orderbook': create_order_book(sorted_shorts, 0.1),
        'long_orders': sorted_longs,
        'short_orders': sorted_shorts
    }


# Archived Data Helper Functions
def read_archived_dataset() -> list[dict]:
    """
    Reads and returns all archived datasets.
    
    This function reads all of the archived datasets and returns them as a list of dictionaries. This function is
    only intended for use in development, as it returns all of the archived data at once.
    
    Returns:
        list[dict]: A list of dictionaries, where each dictionary contains a single archived dataset.
    """    
    dataset = []
    for data in ['dlob','user','market']:
        dataset.append(read_archived_data(data))
    return dataset

def read_archived_data(data_category: str) -> dict:
    """
    Reads and returns the latest archived dataset for a given category.
    
    This function reads the latest archived dataset for a given category, specified by the 'data_category' argument.
    The archived datasets are stored as JSON files, and the function returns the contents of the latest file in the
    appropriate directory.
    
    Args:
        data_category (str): A string specifying the category of data to retrieve. This argument must be one of
            'user', 'market', or 'dlob'.
    
    Returns:
        dict: A dictionary containing the archived dataset for the given category.
    
    Raises:
        Exception: If the input data category is not one of ['user','market','dlob'].
        Exception: If there are no files in the archive for the given data category.
        Exception: If there was a problem reading the data from the file.    """    
    if not data_category in ['user','market','dlob']: 
        raise Exception("RequestError: f{data_category} not read")
    path = os.path.join(data_dir_path(),'archived', data_category)
    filename = os.listdir(path)[-1]
    path = os.path.join(path,filename)
    with open(path, 'r') as f: data = json.load(f)
    return data
    
def delete_oldest_archived(buffer, storage_maxed):
    """Deletes oldest file in each subdirectory of data/archived.

    Deletes the oldest file in each subdirectory of `data/archived`, which includes 'dlob', 'user', and 'market'. 
    If any of the subdirectories do not contain any files, no files will be deleted. 

    Raises:
        FileNotFoundError: If any of the subdirectories in `data/archived` do not exist.
    """
    if buffer % STORAGE_BUFFER == 0 and storage_maxed: 
        for data in ['dlob','user','market']:
            delete_archived_data(data)
            print("Oldest archived {data} deleted. Back up or increase storage")

def delete_archived_data(data_category: str):
    """Deletes the latest archive data file for given data category.

    Deletes the latest archive data file for the given data category within the `data/archived` directory.
    Args:
        data_category (str): The data category for which to delete the latest archive data file. Valid values include 'dlob', 'user', and 'market'.
    Raises:
        FileNotFoundError: If the specified data category does not exist within `data/archived`.
        IndexError: If there are no files to delete in the specified data category.
    """    
    path = os.path.join(data_dir_path(),'archived', data_category)
    filename = os.listdir(path)[0]
    os.remove(os.path.join(path,filename))

def archive_dataset(dataset: list[dict]):
    """Archives list of all datasets to respective directory.

    Archives each dictionary in `dataset` to the appropriate subdirectory within the `data/archived` directory. 
    The appropriate subdirectory is determined based on the contents of each dictionary.
    Args:
        dataset (list[dict]): The list of dictionaries to be archived.
    Raises:
        ValueError: If any of the dictionaries in `dataset` are invalid for archiving.
    """    
    for data in dataset:
        archive_data(data)

def archive_data(data: dict):
    """Archive dataset by creating a timestamped JSON and storing appropriate subdirectory in '/data/archived'.

    Archives the input dictionary by creating a timestamped JSON and storing it in the appropriate subdirectory of the `data/archived` directory.
    The appropriate subdirectory is determined based on the contents of the dictionary.
    Args:
        data (dict): A dictionary representing the data to be archived.
    Raises:
        ValueError: If the input data is not valid for archiving.
    """
    if keyword_in_data(data, ['collateral','leverage']): 
        data_category = 'user'
    elif keyword_in_data(data,['mark', 'spread','twap', 'volume']): 
        data_category = 'market'
    elif keyword_in_data(data,['orderbook']): 
        data_category = 'dlob'
    else:
        raise ValueError("Invalid data dictionary for archiving.")
    #Timestamping and storage
    time_str = time.strftime('%y%m%d-%H:%M')
    filename = f'{data_category}-{time_str}.json'
    path = os.path.join(data_dir_path(),'archived', data_category, filename)
    try: 
        with open(path, 'w') as f: json.dump(data, f)
    except:
        raise TypeError("There is an error with: ", type(data) )

    print(f"{data_category} data archived")
    
def keyword_in_data(data, keywords: list[str]) -> bool:
    """
    Checks if any of the given keywords exist in the data dictionary keys.

    Args:
        data: The data to search through. If it is a list, the first dictionary in the list will be used.
        keywords (list[str]): The list of keywords to search for.

    Returns:
        bool: True if any of the keywords are found in the keys of the data dictionary, False otherwise.
    """    
    d = data if type(data)== dict else data[0]
    for keyword in keywords:
        for key in d.keys():
            if keyword in key: 
                return True
    return False

def make_data_readable(data: Union[dict, list]) -> Union[dict, list]:
    """
    Converts BigNumber values to readable format. Formats
        data extracted from driftpy (Market and User data)
    Args:
        data (Union[dict, list]): Data with values to be converted
        isReadable (bool, optional): Determines whether the returned values are in readable format or not. Defaults to True.
    Returns:
        Union[dict, list]: Data in readable format.
    """
    if type(data) == list:
        readable_data = []
        for i in data:
            readable_data.append(make_data_readable(i))
        return readable_data
    for key in data:
        if ("base" in key or "volume" in key) and not "spread" in key:
            data[key] /= BASE_PRECISION
        elif "fund" in key:
            data[key] /= FUNDING_RATE_PRECISION
        elif "quote" in key:
            data[key] /= QUOTE_PRECISION
        elif("mark" in key or "oracle" in key or "spread" in key or "price" in key
            or "twap" in key or "pnl" or "collateral" in key or "liability" in key
            ):
            data[key] /= PRICE_PRECISION
    return data

def create_order_book(sorted_orders: list[dict], order_tick_size: float = 0.1) -> dict:
    """
    Creates an order book from a list of sorted orders.

    Args:
        sorted_orders (list[dict]): The list of sorted orders.
        order_tick_size (float, optional): The tick size to generate order blocks. Default is 0.05.

    Returns:
        dict: The order book representing either longs or shorts orderbook.
    """
    order_book = {}
    for order in sorted_orders:
        #Round shorts up, Longs round down
        if order['direction'] == 'short':
            group = ((order['price']+ order_tick_size) // order_tick_size) * order_tick_size
        else:
            group = ((order['price']+order_tick_size/100)//order_tick_size) * order_tick_size
        if group not in order_book:
            order_book[str(group)] = {'price': group, 'quantity': order['baseAssetAmount']}
        order_book[str(group)]['quantity'] += order['baseAssetAmount']
        # Create cumulative sum for quantities
        cumulative_quantity = 0
        for price, order in order_book.items():
            cumulative_quantity += order['quantity']
            order['cumulative_quantity'] = cumulative_quantity      
    return order_book

def choose_strategy() -> str:
    """
    Return module name of user requested strategy: First display a list 
    of available strategies and prompts the user to select one to load.
    Pressing any key will select the default strategy.

    Returns:
        Function execution of the class stored inside the given Strategy Class
    """
    # Get a list of all files in the strategies directory
    path = strategies_dir_path()
    files = os.listdir(path)
    # Display strategies
    print('Strategies:\n Choose one of the following strategies')
    i = 0
    strategy_files = []
    # File exclusion list, print remaining files
    for filename in os.listdir(path):
        if "cache" not in filename and "init" not in filename and "base" not in filename:
            strategy_files.append(filename)
        if "default" in filename:
            default_file = filename 
    for i, filename in enumerate(strategy_files):
        print(f"{i+1}. {filename}")
    selection = input("Select strategy # to implement (Press any key for default): ")
    # Check for out of scope inputs, set to default
    if not selection.isdigit() or int(selection) < 1 or int(selection) > len(strategy_files):
        filename = default_file
    else: 
        filename = strategy_files[int(selection)-1]
    filename = default_file
    print(f'Loading strategy...: {filename}')
    module_name = filename[:-3]  # Remove ".py" extension
    module = importlib.import_module(f'strategies.{module_name}')
    strategy_class = getattr(module, 'DefaultStrategy')
    return strategy_class

def update_prices(orders: list[dict]) -> list[dict]:
    """
    Updates entries for orders with price 0 in the given list of orders.

    Args:
        orders (list[dict]): The list of orders to update.

    Returns:
        list[dict]: The updated list of orders.
    """    
    updated_orders = deepcopy(orders)
    for i, order in enumerate(orders):
        if updated_orders[i]['price'] == 0:
            updated_orders[i]['price'] = order['oracle_price'] + order['oraclePriceOffset']
    return updated_orders

def filter_orders(orders: list[dict], filter: str='long', param: str='direction'):
    """Filters a list of orders by the given field.

    Args:
        orders (list[dict]): The list of orders to filter.
        filter (str, optional): The value to filter by. Default is 'long'.
        param (str, optional): The name of the field to filter by. Default is 'direction'.

    Returns:
        list[dict]: The filtered list of orders.
    """    
    return [order for order in orders if order[param] == filter]

def get_dir_path(dir_name: str) -> str:
    """
    Returns the absolute path of the requested directory.

    Args:
        dir_name (str): The name of the directory.

    Returns:
        str: The absolute path of the requested directory.

    Raises:
        Exception: If the directory name does not exist.
    """    
    if dir_name == 'data' or dir_name == 'js_src' or dir_name == 'src':
        return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', dir_name))
    elif dir_name == 'strategies' or dir_name == 'tests':
        return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src', dir_name))
    else:
        raise Exception("NameError: Directory does not exist ")
    # unimplemented

def print_all_data(dlob_data: list[dict], user_data: dict, market_data: dict):
    """
    Formatted print of the datasets to the console.

    Args:
        dlob_data (list[dict]): The list of dictionaries that represent the data for the order book.
        user_data (dict): The dictionary that represents the data for the market maker user.
        market_data (dict): The dictionary that represents the market data.
    """
    
    sum = len(dlob_data['long_orderbook']) + len(dlob_data['short_orderbook'])
    print("OrderBook:")
    print("Highest bid: ", f"{dlob_data['best_bid']:.3f}",
     "Lowest ask: ", f"{dlob_data['best_ask']:.3f}, # Limit Orders: {sum}")
    print("\nOrderbook Bids:"), print_ob(dlob_data['long_orderbook'])
    print("Orderbook Asks:"), print_ob(dlob_data['short_orderbook']) 
    console_line()   
    print("Market Maker User Data: \n", user_data) 
    console_line()
    print(MARKET_NAME,"Market Data:\n", market_data)
    console_line()

def print_orders(dlob: list[dict], maxprints: int = 3):
    """Formatted printing of dlob orders upto maxprints.
     Args:
        dlob (list[dict]): The list of dictionaries that represent the data for the order book.
        maxprints (int, optional): The maximum number of orders to print. Defaults to 3.
    """
    for i, order in enumerate(dlob):
        if(i == maxprints):
            break
        else:
            print(order,'\n')

def print_ob(order_book, max_print: int = 5):
    """Prints order book to console.

    Args:
        order_book (dict): The dictionary that represents the data for the order book.
        max_print (int): Maximum orderbook items printed to console
    """
    counter = 0
    for key, value in order_book.items():
        if counter == max_print:
            break
        if type(value['price']) == float:
            p = f"{value['price']:.2f}"
            q = f"{value['quantity']:.2f}"
            c_q = f"{value['cumulative_quantity']:.2f}"
            print(f"price: {p}, quantity: {q}, cumulative_quantity: {c_q}")
        else: print(value)
        counter += 1

def console_line() -> None:
    """Prints separator line in console"""
    print('------------------------------------------------------------------')
