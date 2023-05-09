"""Changelog: test directory moved to src/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__),'..','src')))
print(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__),'..')))
"""

#import pytest
import sys
import os
import asyncio
from drifttest_driftclient import Drifttest_driftclient

test_driftclient = DriftClient()

def test_init():
    print(type(test_driftclient.acct))
    print(type(test_driftclient.chu))
    print(type(test_driftclient.orders))
    print(test_driftclient.default_order)

def test_get_accounts(display = False):
    return test_driftclient.get_accounts(display)

async def test_user_margin_enabled():
    data = await test_driftclient.get_user_data()
    """ Test code:
    loop = asyncio.get_event_loop()
    x= loop.run_until_complete(test_user_margin_enabled())
    print(x)"""
    return data
    
async def test_get_market_data(isReadable: bool = True, fullData: bool = False):
    perp_data = await test_driftclient.get_market_data(isReadable,fullData)
    #loop = asyncio.get_event_loop()
    #perp_data = loop.run_until_complete(test_driftclient.get_market_data(isReadable,fullData))
    print(perp_data)
    #return perp_data

async def measure_time(driftclient: DriftClient):
    start_time = asyncio.get_running_loop().time()
    task = asyncio.create_task(driftclient.get_driftuser_data())
    try:
        await asyncio.wait_for(task, timeout=20)
    except asyncio.TimeoutError:
        print("Timeout!")
    end_time = asyncio.get_running_loop().time()
    print(f"Time taken: {end_time - start_time:.2f} seconds")    

async def test_get_driftuser_data():
    test_driftclient.get_driftuser_data()

async def test_perpmarket_print():
    test_driftclient.perpmarket_print()

asyncio.run(test_get_market_data(True,True))
#asyncio.run(test_get_market_data(True,False))

async def test_get_driftuser_data():
    await test_driftclient.get_driftuser_data()

x = asyncio.run(test_driftclient.get_market_data())
print(x)