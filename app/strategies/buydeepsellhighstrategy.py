from strategies.istrategyinterface import  IStrategyInterface
from messages.python.strategyconfigmessage import StrategyConfigMessage, StrategyConfig
from exchanges.binance_order_interface import Binance_Order_Interface
from exchanges.testorderinterface import TestOrderInterface

from binance.enums import *
from abc import ABC, abstractmethod

class Level:
    def __init__(self, percent, qty):
        self.qty = qty
        self.percent = percent
        self.is_done = False
        self.done_qty = 0.0
        self.fill_price = 0.0


class PerCryptoStatus:
    def __init__(self, strategy_confg):
        self.crypto = strategy_confg.crypto
        self.is_first_order_complete = False
        self.base_price = 0.0
        self.qty_lvl_zero_qty = strategy_confg.qty_lvl_zero_qty
        self.exit_percentage = strategy_confg.exit_percentage
        self.qty_unit = strategy_confg.qty_unit
        self.symbol = strategy_confg.crypto
        self.lavel_data = []
        for level in strategy_confg.levels:
            self.lavel_data.append(Level(level[0], level[1]))


class BuyDeepSellHighStrategy(IStrategyInterface):
    def __init__(self, message, is_test):
        self.config_data = message
        if not is_test:
            self.exchnage_interface = Binance_Order_Interface(message)
        else:
            self.exchnage_interface = TestOrderInterface(message)

        self.per_crypto_status = {}
        for key, strategy_confg in message.configurationsmap.items():
            per_crypto_state = PerCryptoStatus(strategy_confg)
            self.per_crypto_status[per_crypto_state.crypto] = per_crypto_state


    #to be used only for test
    def get_exchange_interface(self):
        return self.exchnage_interface

    def on_start(self, jsonemessage):
        #read bot status from db
        pass
   
    def reset_strategy(self, per_crypto_status):
        per_crypto_status.base_price = 0.0
        per_crypto_status.is_first_order_complete = False
        for level in per_crypto_status.lavel_data:
            level.is_done = False
            level.done_qty = 0.0
            level.fill_price = 0.0


    def on_market_data_update(self, marketDataMessage):
        val = self.per_crypto_status.get(marketDataMessage.symbol)

        if None == val:
            return None
        if not self.exchnage_interface.is_initialized:
            return None

        if not val.is_first_order_complete:
            order = self.exchnage_interface.send_order(val.crypto, True, val.qty_lvl_zero_qty*val.qty_unit, 0, True) 
            if order is not None:
                if order['status'] == 'FILLED':
                    val.is_first_order_complete = True
                    val.base_price = float(order['fills'][0]['price'])
                    print("First order complete at price:" + str(val.base_price))
                    #store bot status in  db, in case bot restarts we should have status as when it went down
        else:
            #check if we can see
            target_percent = ((marketDataMessage.price - val.base_price)*100)/val.base_price
            print("target_percent:" + str(target_percent))
            qty = 0
            if target_percent > val.exit_percentage:
                for level in val.lavel_data:
                    qty += level.done_qty
                if qty > 0:
                    order = self.exchnage_interface.send_order(val.crypto, False, qty, 0.0, True)
                    if order['status'] == 'FILLED':
                        #sell is filled resetting the algo, will start fresh from now
                        self.reset_strategy(val)
                        self.on_market_data_update(marketDataMessage)
                        return (True, qty, 0)
            else:
                qty = 0
                for level in val.lavel_data:
                    if level.is_done: continue
                    if target_percent < 0:
                        if abs(target_percent) >= level.percent:
                            buy_qty = level.qty * val.qty_unit;
                            order = self.exchnage_interface.send_order(val.crypto, True, buy_qty, 0, True)
                            if order is not None:
                                if order['status'] == 'FILLED':
                                    level.is_done = True
                                    for fill in order['fills']:
                                        level.fill_price = float(fill['price'])
                                        level.done_qty += float(fill['qty'])
                                        qty += level.done_qty
            if qty > 0:
                return (False, qty, 0)
        return None

    def on_configuration_update(self, configUpdateMessage):
        pass
