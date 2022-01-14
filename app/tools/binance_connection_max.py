import asyncio
import copy
import json
import threading
import time
from multiprocessing import Process
from types import SimpleNamespace
from binance import Client, AsyncClient, ThreadedWebsocketManager, ThreadedDepthCacheManager, BinanceSocketManager
from binance.enums import *
from binance.exceptions import BinanceAPIException

max_conn = 100

clients = {}

Client_Api_Key = "aP0q0oEd7q5BPXVOWAans2yssuM2ZtlSDVv8QPOSUqYkxSeACZhnlgdGgsNkRbhC"
Client_Api_Key2 = "MHdyNt5uKjfq42oGpo0cUHUDKoZ1evfnZTt4KqwZ004FQnRUBwT9nGV7TrGpXfse"

for idx in range(0, 100, 1):
    try:
        print(idx)
        client2 = Client(Client_Api_Key,  Client_Api_Key2, testnet=True)
        clients[idx] = client2
        account = client2.get_account()
        print(account)
        time.sleep(5)
    except Exception as e:
        print(e)


""" class Binance_Async_Interface:
    def __init__(self, message, queue):
        self.message = message
        self.queue = queue
        self.client = None
        self.account_bal_usd = None
        self.initialized = False
        self.account = None
        self.exechange_info = None
        self.orders = []

    def send_error_to_queue(self, res):
        res["Type"] = "BinanceErrorOccured"
        res["Client"] = self.message.clinet_details.Client_Id
        self.queue.put(res)

    async def create(self):
        try:
            c
            self.account = await self.client.get_account()
            self.exechange_info = await self.client.get_exchange_info()
            acct_to_send = copy.deepcopy(self.account)
            acct_to_send["Type"] = "ExchangeResponseAccount"
            acct_to_send["Client"] = self.message.clinet_details.Client_Id
            self.queue.put(acct_to_send)
            #print(acct_to_send)
            #json_object = json.dumps(acct_to_send, indent = 4)
        except BinanceAPIException as e:
            res = {}
            res["Description"] = str(e)
            res["Reason"] = "create"
            self.send_error_to_queue(res)
            #print(res)
            
        except Exception as e:
            res = {}
            res["Description"] = str(e)
            res["Reason"] = "create"
            self.send_error_to_queue(res)
            #print(res)
        else:
           self.initialized = True

    def get_precision(self, crypto):
        for x in self.exechange_info['symbols']:
            if x['symbol'] == crypto:
                for c in x['filters']:
                    if c['filterType'] == 'PRICE_FILTER':
                        return (c['tickSize'].find('1') - 1)



    async def send_order_cancel_status(self, res):
        res["Client"] = self.message.clinet_details.Client_Id
        res["Type"] = "OrderCancelResponse"
        self.queue.put(res)
        

    async def handle_execution_response(self, res, client2):
        res["Client"] = self.message.clinet_details.Client_Id        
        if res["e"] == "outboundAccountPosition":
            res["Type"] = "ExchangeResponseAccount"
            self.queue.put(res)
        elif res["e"] == "balanceUpdate":
            res["Type"] = "BalanceExchangeResponse"
            self.queue.put(res)
        elif res["e"] == "executionReport":
            #print(f"res: {res}")
            symbol = res["s"]
            order_id = int(res["i"])
            order = await client2.get_order(symbol=symbol, orderId = order_id)
            order["Type"] = "OrderStatus"
            order["Client"] = self.message.clinet_details.Client_Id        
            order["LastExcutionPrice"] = res["L"]
            order["CurrentStatus"] = res["X"]
            self.queue.put(order)
        else:
            print(f"unknown: {res}")

    async def wait_on_user(self):
        try:
            client2 = await AsyncClient.create(self.message.clinet_details.Client_Api_Key, self.message.clinet_details.Client_Api_Key2, testnet=self.message.IsTestNet)
            binance_socket_manager = BinanceSocketManager(client2)
            user_socket = binance_socket_manager.user_socket()
            async with user_socket as scoped_user_socket:
                while True:
                    #print("waiting............................")
                    res = await scoped_user_socket.recv()
                    if res is not None:
                        await self.handle_execution_response(res, client2)
                    else:
                        print("Time out")

        except BinanceAPIException as e:
            res = {}
            res["Description"] = str(e)
            res["Reason"] = "wait_on_user"
            self.send_error_to_queue(res)
            #print(res)
        except Exception as e:
            res = {}
            res["Description"] = str(e)
            res["Reason"] = "wait_on_user"
            self.send_error_to_queue(res)
            #print(res)

        await self.client.close_connection()        

    async def send_mkt_order(self, crypto_symbol, side, qty):
        try:
            order = await self.client.create_order(symbol=crypto_symbol, side=side, type=ORDER_TYPE_MARKET,  quantity=qty)
            return order
        except BinanceAPIException as e:
            res = {}
            res["Description"] = str(e)
            res["Reason"] = "send_order"
            res["Symbol"] = crypto_symbol
            res["Side"] = side
            res["Qty"] = qty
            self.send_error_to_queue(res)
            #print(res)

            return None
        except Exception as e:
            res = {}
            res["Description"] = str(e)
            res["Reason"] = "send_order"
            res["Symbol"] = crypto_symbol
            res["Side"] = side
            res["Qty"] = qty
            self.send_error_to_queue(res)
            #print(res)
            return None

    async def send_order(self, crypto_symbol, side, type, timeInForce, qty, price):
        try:
            price = round(price, self.get_precision(crypto_symbol)) #ToDo check pricision and send price 
            order = await self.client.create_order(symbol=crypto_symbol, side=side, type=type, timeInForce=timeInForce, quantity=qty, price=str(price))
            return order
        except BinanceAPIException as e:
            res = {}
            res["Description"] = str(e)
            res["Reason"] = "send_order"
            res["Symbol"] = crypto_symbol
            res["Side"] = side
            res["Qty"] = qty
            res["price"] = price
            self.send_error_to_queue(res)
            #print(res)

            return None
        except Exception as e:
            res = {}
            res["Description"] = str(e)
            res["Reason"] = "send_order"
            res["Symbol"] = crypto_symbol
            res["Side"] = side
            res["Qty"] = qty
            res["price"] = price
            self.send_error_to_queue(res)
            #print(res)
            return None


    async def cancel_all(self):
        try:
            orders = await self.client.get_open_orders()
            for ord in orders:
                res = await self.client.cancel_order(symbol=ord['symbol'], orderId=ord['orderId'])
                self.send_order_cancel_status(res)
                #print(res)
            return True
        except BinanceAPIException as e:
            self.send_error_to_queue(e)            
            return False
            #print(e)
        except Exception as e:
            self.send_error_to_queue(e)            
            return False
            #print(e)


        #print('cancel_all')

    def bridge_func(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.wait_on_user())
        loop.close()
        
 """