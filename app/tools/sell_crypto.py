import asyncio
import copy
import json
import multiprocessing
from os import path
import threading
import time
from pathlib import Path

from multiprocessing import Process
from types import SimpleNamespace
from binance import Client, AsyncClient, ThreadedWebsocketManager, ThreadedDepthCacheManager, BinanceSocketManager
from binance.enums import *
from binance.exceptions import BinanceAPIException
#from exchanges.binance_async_interface import Binance_Async_Interface
#import  messaging.kafka_messaging



async def sell_crypto():

    client = await AsyncClient.create('aP0q0oEd7q5BPXVOWAans2yssuM2ZtlSDVv8QPOSUqYkxSeACZhnlgdGgsNkRbhC', 'MHdyNt5uKjfq42oGpo0cUHUDKoZ1evfnZTt4KqwZ004FQnRUBwT9nGV7TrGpXfse', testnet=True)
    account = await client.get_account()
    print(account)

    print('*********************************************************************')
    orders = await client.get_open_orders()
    print(orders)
    print('*********************************************************************')
    for ord in orders:
        res = await client.cancel_order(symbol=ord['symbol'], orderId=ord['orderId'])
        print(f"can: {res}")
    print('*********************************************************************')
    orders = await client.get_open_orders()
    print(orders)                
    
    print('*********************************************************************')
    #order = await client.create_order(symbol='ETHUSDT', side=SIDE_SELL, type=ORDER_TYPE_LIMIT, quantity=60, timeInForce= TIME_IN_FORCE_GTC, price=99.76000000)
    #print(order)
    #order = await client.create_order(symbol='BNBUSDT', side=SIDE_SELL, type=ORDER_TYPE_LIMIT, quantity=10, timeInForce= TIME_IN_FORCE_GTC, price=521)
    while True:
        order = await client.create_order(symbol='BNBUSDT', side=SIDE_SELL, type=ORDER_TYPE_MARKET, quantity=1000)
        print(order)
        print('*********************************************************************')

    account = await client.get_account()
    print(account)
    print('*********************************************************************')
    orders = await client.get_open_orders()
    print(orders)
    print('*********************************************************************')
    


loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
loop.run_until_complete(sell_crypto())
loop.close()
