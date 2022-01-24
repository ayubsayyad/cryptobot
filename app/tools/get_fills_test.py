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
account = client.get_account()
print(account)

orders = client.get_my_trades(symbol='BNBUSDT')
print(orders)


#ord = client.get_order(symbol='BNBUSDT', orderId=2542239)
#print(ord)

#order = client.create_order(symbol='BNBUSDT', side=SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=0.1)
#print(order)
#print('*********************************************************************')


