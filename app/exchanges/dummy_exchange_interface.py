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


class DummyExchangeInterface:
    def __init__(self, message, queue):
        self.message = message
        self.queue = queue
        self.client = None
        self.account_bal_usd = None
        self.account = None
        self.exchange_info = None
        self.orders = []
        self.initialized = True
        self.last_orders = []
        self.last_mkt_order = None


    def get_price_precision(self, crypto):
        return '0.00000100'.find('1') - 1

    def get_qty_precision(self, crypto):
        return '0.00000100'.find('1') - 1
        return None

    def send_error_to_queue(self, res):
        res["Type"] = "BinanceErrorOccurred"
        res["Client"] = self.message.clinet_details.Client_Id
        self.queue.put(res)

    def create(self):
        self.initialized = True

    def get_precision(self, crypto):
        pass

    def get_price_for_crypto_in_usd(self, symbol):
        # redis details needed from Dan
        if symbol == "BTCUSDT":
            return 43005.91
        elif symbol == "BNBUSDT":
            return 493.0
        elif symbol == "MATICUSDT":
            return 2.290
        return None

    def send_mkt_order(self, crypto_symbol, side, qty):
        order_response = {'symbol': crypto_symbol, 'orderId': 1, 'orderListId': -1,
                          'clientOrderId': 'wPJ4k9kJJ6tG3i2vstcwIb', 'transactTime': 1641361224365,
                          'price': '0.00000000',
                          'origQty': str(qty), 'executedQty': str(qty), 'cummulativeQuoteQty': '231.26485000',
                          'status': 'FILLED', 'timeInForce': 'GTC', 'type': 'MARKET', 'side': side}

        price = str(self.get_price_for_crypto_in_usd(crypto_symbol))
        fill1 = {'price': price, 'qty': str(qty), 'commission': '0.00000000', 'commissionAsset': 'BTC',
                 'tradeId': 2}

        fills = [fill1]

        order_response['fills'] = fills

        self.last_mkt_order = order_response
        return order_response

    def cancel_all(self, symbol):
        return True

        # print('cancel_all')

    def send_order_cancel_status(self, res):
        res["Client"] = self.message.clinet_details.Client_Id
        res["Type"] = "OrderCancelResponse"
        self.queue.put(res)

    def handle_execution_response(self, res, client2):
        pass

    def wait_on_user(self):
        pass

    def send_order(self, crypto_symbol, side, order_type, time_in_force, qty, price):
        order_response = {'symbol': crypto_symbol, 'orderId': 1, 'orderListId': -1,
                          'clientOrderId': 'wPJ4k9kJJ6tG3i2vstcwIb', 'transactTime': 1641361224365,
                          'price': '0.00000000',
                          'origQty': str(qty), 'executedQty': str(qty), 'cummulativeQuoteQty': '231.26485000',
                          'status': 'NEW', 'timeInForce': 'GTC', 'type': 'LIMIT', 'side': side}

        self.last_orders.append(order_response)
        return order_response

    def bridge_func(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.wait_on_user())
        loop.close()
