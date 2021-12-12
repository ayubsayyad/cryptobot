from strategies.istrategyinterface import  IStrategyInterface
from messages.python.strategyconfigmessage import StrategyConfigMessage
from exchanges.binance_order_interface import Binance_Order_Interface
from exchanges.test_order_interface import Test_Order_Interface

from binance.enums import *
from abc import ABC, abstractmethod

class Level:
    def __init__(self, percent, qty):
        self.qty = qty
        self.percent = percent
        self.is_done = False
        self.done_qty = 0.0
        self.fill_price = 0.0

class BuyDeepSellHighStrategy(IStrategyInterface):
    def __init__(self, message, is_test):
        self.config_data = message
        if not is_test:
            self.exchnage_interface = Binance_Order_Interface(message)
        else:
            self.exchnage_interface = Test_Order_Interface(message)

        self.is_first_order_complete = False
        self.base_price = 0.0
        self.exit_percentage = message.exit_percentage
        self.qty_unit = message.qty_unit
        self.symbol = message.symbol
        self.lavel_data = []
        for level in message.levels:
            self.lavel_data.append(Level(level[0], level[1]))

    #to be used only for test
    def get_exchange_interface(self):
        return self.exchnage_interface

    def on_start(self, jsonemessage):
        #read bot status from db
        pass
   
    def reset_strategy(self):
        self.base_price = 0.0
        self.is_first_order_complete = False
        for level in self.lavel_data:
            level.is_done = False
            level.done_qty = 0.0
            level.fill_price = 0.0


    def on_market_data_update(self, marketDataMessage):
        if marketDataMessage.symbol != self.symbol:
            return None
        if not self.exchnage_interface.is_initialized:
            return None

        if not self.is_first_order_complete:
            order = self.exchnage_interface.send_order(True, self.config_data.qty_lvl_zero_qty*self.qty_unit, 0, True) 
            if order is not None:
                if order['status'] == 'FILLED':
                    self.is_first_order_complete = True
                    self.base_price = float(order['fills'][0]['price'])
                    print("First order complete at price:" + str(self.base_price))
                    #store bot status in  db, in case bot restarts we should have status as when it went down
        else:
            #check if we can see
            target_percent = ((marketDataMessage.price - self.base_price)*100)/self.base_price
            print("target_percent:" + str(target_percent))
            qty = 0
            if target_percent > self.exit_percentage:
                for level in self.lavel_data:
                    qty += level.done_qty
                if qty > 0:
                    order = self.exchnage_interface.send_order(False, qty, 0.0, True)
                    if order['status'] == 'FILLED':
                        #sell is filled resetting the algo, will start fresh from now
                        self.reset_strategy()
                        return (True, qty, 0)
            else:
                qty = 0
                for level in self.lavel_data:
                    if level.is_done: continue
                    if target_percent < 0:
                        if abs(target_percent) >= level.percent:
                            buy_qty = level.qty * self.qty_unit;
                            order = self.exchnage_interface.send_order(True, buy_qty, 0, True)
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
