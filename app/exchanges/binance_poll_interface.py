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


class BinancePollInterface:
    def __init__(self, message, queue):
        self.message = message
        self.queue = queue
        self.client = None
        self.account_bal_usd = None
        self.initialized = False
        self.account = None
        self.exchange_info = None
        self.orders = []

    def send_error_to_queue(self, res):
        res["Type"] = "BinanceErrorOccurred"
        res["Client"] = self.message.clinet_details.Client_Id
        self.queue.put(res)

    def create(self):
        try:
            self.client = Client(self.message.clinet_details.Client_Api_Key,
                                 self.message.clinet_details.Client_Api_Key2, testnet=self.message.IsTestNet)
            self.account = self.client.get_account()
            self.exchange_info = self.client.get_exchange_info()
            acct_to_send = copy.deepcopy(self.account)
            acct_to_send["Type"] = "ExchangeResponseAccount"
            acct_to_send["Client"] = self.message.clinet_details.Client_Id
            self.queue.put(acct_to_send)
            # print(acct_to_send)
            # json_object = json.dumps(acct_to_send, indent = 4)
        except BinanceAPIException as e:
            res = {"Description": str(e), "Reason": "create"}
            self.send_error_to_queue(res)
            # print(res)

        except Exception as e:
            res = {"Description": str(e), "Reason": "create"}
            self.send_error_to_queue(res)
            # print(res)
        else:
            self.initialized = True

    def get_price_precision(self, crypto):
        for x in self.exechange_info['symbols']:
            if x['symbol'] == crypto:
                for c in x['filters']:
                    if c['filterType'] == 'PRICE_FILTER':
                        return c['tickSize'].find('1') - 1

        return None

    def get_qty_precision(self, crypto):
        for x in self.exechange_info['symbols']:
            if x['symbol'] == crypto:
                for c in x['filters']:
                    if c['filterType'] == 'LOT_SIZE':
                        return c['stepSize'].find('1') - 1

        return None

    def send_order_cancel_status(self, res):
        res["Client"] = self.message.clinet_details.Client_Id
        res["Type"] = "OrderCancelResponse"
        self.queue.put(res)

    def get_client_trades(self, symbol):
        trades = self.client.get_my_trades(symbol=symbol)
        return trades

    def send_mkt_order(self, crypto_symbol, side, qty):
        try:
            order = self.client.create_order(symbol=crypto_symbol, side=side, type=ORDER_TYPE_MARKET, quantity=qty)
            return order
        except BinanceAPIException as e:
            res = {"Description": str(e), "Reason": "send_order", "Symbol": crypto_symbol, "Side": side, "Qty": qty}
            self.send_error_to_queue(res)
            # print(res)

            return None
        except Exception as e:
            res = {"Description": str(e), "Reason": "send_order", "Symbol": crypto_symbol, "Side": side, "Qty": qty}
            self.send_error_to_queue(res)
            # print(res)
            return None

    def get_client_order(self, ord_symbol, order_id):
        return self.client.get_order(symbol=ord_symbol, orderId=order_id)

    def send_order(self, crypto_symbol, side, order_type, time_in_force, qty, price):
        try:
            price = round(price, self.get_price_precision(crypto_symbol))
            qty = round(qty, self.get_qty_precision(crypto_symbol))
            order = self.client.create_order(symbol=crypto_symbol, side=side, type=order_type, timeInForce=time_in_force,
                                             quantity=qty, price=str(price))
            return order
        except BinanceAPIException as e:
            res = {"Description": str(e), "Reason": "send_order", "Symbol": crypto_symbol, "Side": side, "Qty": qty,
                   "price": price}
            self.send_error_to_queue(res)
            return None

        except Exception as e:
            res = {"Description": str(e), "Reason": "send_order", "Symbol": crypto_symbol, "Side": side, "Qty": qty,
                   "price": price}
            self.send_error_to_queue(res)
            return None

    def cancel_all(self, symbol):
        try:
            orders = self.client.get_open_orders()
            for order in orders:
                if order['symbol'] == symbol:
                    res = self.client.cancel_order(symbol=order['symbol'], orderId=order['orderId'])
                    self.send_order_cancel_status(res)
                    # print(res)
            return True
        except BinanceAPIException as e:
            self.send_error_to_queue(e)
            return False
            # print(e)
        except Exception as e:
            self.send_error_to_queue(e)
            return False
            # print(e)
