from binance import Client, ThreadedWebsocketManager, ThreadedDepthCacheManager
from binance.enums import *


class TestOrderInterface:
    def __init__(self, message):
        self.message = message
        self.client = None
        self.account_bal_usd = None
        self.initialized = False
        self.orders = []
        self.initialized = True

    def get_account_balance(self):
        return self.account_bal_usd

    def is_initialized(self):
        return self.is_initialized

    def send_order(self, crypto_symbol, is_buy, qty, price, is_mkt):
        if not self.initialized:
            return None

        if is_buy:
            print("Buying:" + str(qty))
        else:
            print("Selling:" + str(qty))

        order = {'status': 'FILLED'}
        fills = {'price': 49000, 'qty': qty}
        order['fills'] = [fills]
        return order
