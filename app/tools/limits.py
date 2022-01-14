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

import asyncio
from binance import AsyncClient, BinanceSocketManager


client = Client('aP0q0oEd7q5BPXVOWAans2yssuM2ZtlSDVv8QPOSUqYkxSeACZhnlgdGgsNkRbhC', 'MHdyNt5uKjfq42oGpo0cUHUDKoZ1evfnZTt4KqwZ004FQnRUBwT9nGV7TrGpXfse', testnet=True)
#while True:

#    account = client.get_account()
#    account = client.get_exchange_info()
#    print(client.response.headers)
#    time.sleep(1)

#print(account)
#print("**********************")
#account = client.get_exchange_info()
#account = client.get_exchange_info()
#account = client.get_exchange_info()
#print(client.response.headers)
#print("**********************")
#print(account)
#print("**********************")
#account = client.get_account_snapshot(type="SPOT")
#account = client.get_exchange_info()
#print(client.response.headers)
#print("**********************")





async def main():
#    client = await AsyncClient.create()
    bm = BinanceSocketManager(client)
    # start any sockets here, i.e a trade socket
    ts = bm.trade_socket('BTCUSDT')
    # then start receiving messages
    async with ts as tscm:
        print("wait")
        while True:
            res = await tscm.recv()
            print(res)

    await client.close_connection()

if __name__ == "__main__":

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

trade_socket
