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

class Binance_Poll_Interface:
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

    def create(self):
        try:
            self.client = Client(self.message.clinet_details.Client_Api_Key, self.message.clinet_details.Client_Api_Key2, testnet=self.message.IsTestNet)
            self.account = self.client.get_account()
            self.exechange_info = self.client.get_exchange_info()
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

    def send_order_cancel_status(self, res):
        res["Client"] = self.message.clinet_details.Client_Id
        res["Type"] = "OrderCancelResponse"
        self.queue.put(res)
        


    def get_client_trades(self, symbol):
        trades = self.client.get_my_trades(symbol=symbol)
        return trades

    def send_mkt_order(self, crypto_symbol, side, qty):
        try:
            order = self.client.create_order(symbol=crypto_symbol, side=side, type=ORDER_TYPE_MARKET,  quantity=qty)
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

    def send_order(self, crypto_symbol, side, type, timeInForce, qty, price):
        try:
            price = round(price, self.get_precision(crypto_symbol)) #ToDo check pricision and send price 
            order = self.client.create_order(symbol=crypto_symbol, side=side, type=type, timeInForce=timeInForce, quantity=qty, price=str(price))
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


    def cancel_all(self):
        try:
            orders = self.client.get_open_orders()
            for ord in orders:
                res = self.client.cancel_order(symbol=ord['symbol'], orderId=ord['orderId'])
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


