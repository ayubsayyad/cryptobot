from binance import Client, ThreadedWebsocketManager, ThreadedDepthCacheManager
from binance.enums import *


class Binance_Order_Interface:
    def __init__(self, message):
        self.message = message
        self.client = None
        self.account_bal_usd = None
        self.initialized = False
        self.orders = []
        try:
            self.essage.client_api_key
            self.client = Client(message.client_api_key, sage.client_api_key2, testnet=True)
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

    def send_order(self, is_buy, qty, price, is_mkt):
        if not self.initialized:
            return None
        side = SIDE_BUY
        if not is_buy:
            side = SIDE_SELL

        try:
            order = None
            if is_mkt:
                order = client.create_order(symbol=self.message.symbol, side=side, type=ORDER_TYPE_MARKET, quantity=qty)
            else:
                order = client.create_order(symbol=self.message.symbol, side=side, type=ORDER_TYPE_LIMIT, timeInForce=TIME_IN_FORCE_GTC, quantity=qty, price=str(price))
            if order is not None:
                self.orders.append(order)
            return order
        except BinanceAPIException as e:
            print(e)
            return None

