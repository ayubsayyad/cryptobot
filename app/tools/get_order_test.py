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




client = Client('aP0q0oEd7q5BPXVOWAans2yssuM2ZtlSDVv8QPOSUqYkxSeACZhnlgdGgsNkRbhC', 'MHdyNt5uKjfq42oGpo0cUHUDKoZ1evfnZTt4KqwZ004FQnRUBwT9nGV7TrGpXfse', testnet=True)
#client = Client('EEH6GRZJTQE6jhVRPxUoyLTFGBSxBCqqKaAokxj6ztzrHeV25Mc0NF7WmIswHRvl', 'x3x07BYPGEdj9vTRh1BM7bjWm9n9OAx5jwJAqXdDsOq6rM4EjKANqF8DaKVtSsQ5', tld='us')
account = client.get_account()
print(account)

orders = client.get_open_orders()
print(orders)


#ord = client.get_order(symbol='BNBUSDT', orderId=2542239)
#print(ord)

#order = client.create_order(symbol='BNBUSDT', side=SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=0.1)
#print(order)
#print('*********************************************************************')


