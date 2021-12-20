from binance import Client, ThreadedWebsocketManager, ThreadedDepthCacheManager
from binance.enums import *
from binance.exceptions import BinanceAPIException


class Binance_Order_Interface:
    def __init__(self, message):
        self.message = message
        self.client = None
        self.account_bal_usd = None
        self.initialized = False
        self.orders = []
        try:
            self.message.client_api_key
            self.client = Client(message.client_api_key, message.client_api_key2, testnet=True)
            self.account = self.client.get_account()
            for balances in self.account["balances"]:
                if balances['asset'] == 'USDT':
                    self.account_bal_usd = float(balances['free'])
        except BinanceAPIException as e:
            print(e)
        else:
           self.initialized = True

    def get_account_balance(self):
        return self.account_bal_usd

    def is_initialized(self):
        return self.is_initialized

    def send_order(self, crypto_symbol, is_buy, qty, price, is_mkt):
        if not self.initialized:
            return None
        side = SIDE_BUY
        if not is_buy:
            side = SIDE_SELL

        print(crypto_symbol)
        try:
            order = None
            if is_mkt:
                order = self.client.create_order(symbol=crypto_symbol, side=side, type=ORDER_TYPE_MARKET, quantity=qty)
            else:
                order = self.lient.create_order(symbol=crypto_symbol, side=side, type=ORDER_TYPE_LIMIT, timeInForce=TIME_IN_FORCE_GTC, quantity=qty, price=str(price))
            if order is not None:
                self.orders.append(order)
            return order
        except BinanceAPIException as e:
            print(e)
            return None

