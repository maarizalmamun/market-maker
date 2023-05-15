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

"""

import unittest
import asyncio
from unittest.mock import MagicMock, patch
from src.driftclient import DriftClient, MMOrder, Orders
from driftpy.clearing_house import ClearingHouse
from driftpy.clearing_house_user import ClearingHouseUser

class TestDriftClient(unittest.TestCase):
    @patch('src.driftclient.ClearingHouse')
    @patch('src.driftclient.ClearingHouseUser')
    def setUp(self, mock_chu, mock_ch):
        self.keypath = "dummy_path"
        self.client = DriftClient(self.keypath)

        self.mock_chu = mock_chu
        self.mock_ch = mock_ch

        self.client.chu = self.mock_chu
        self.client.drift_acct = self.mock_ch

    def test_get_accounts(self):
        self.client.get_accounts(printkeys=False)
        self.assertTrue(self.mock_ch.get_state_public_key.called)
        self.assertTrue(self.mock_ch.get_user_stats_public_key.called)
        self.assertTrue(self.mock_ch.get_user_account_public_key.called)

    @patch('src.driftclient.asyncio.gather')
    @patch('src.driftclient.get_perp_market_account')
    def test_fetch_chu_data(self, mock_get_perp_market_account, mock_gather):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.client.fetch_chu_data())
        self.assertTrue(mock_gather.called)
        self.assertTrue(mock_get_perp_market_account.called)

class TestMMOrder(unittest.TestCase):
    def setUp(self):
        self.mmorder = MMOrder()

    def test_init(self):
        self.assertIsNotNone(self.mmorder.orderparams)

class TestOrders(unittest.TestCase):
    @patch('src.driftclient.ClearingHouse')
    def setUp(self, mock_ch):
        self.orders = Orders(mock_ch)

        self.mock_ch = mock_ch

    def test_add_order(self):
        mmorder = MMOrder()
        self.orders.add_order(mmorder)
        self.assertEqual(len(self.orders.orders), 1)

    @patch('src.driftclient.ClearingHouse.get_place_perp_order_ix')
    def test_send_orders(self, mock_get_place_perp_order_ix):
        loop = asyncio.get_event_loop()
        mmorder = MMOrder()
        self.orders.add_order(mmorder)
        loop.run_until_complete(self.orders.send_orders())
        self.assertTrue(mock_get_place_perp_order_ix.called)
        self.assertTrue(self.mock_ch.send_ixs.called)

if __name__ == '__main__':
    unittest.main()




"""