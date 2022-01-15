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
from binance.exceptions import BinanceAPIException
from exchanges.binance_poll_interface import BinancePollInterface
from messaging.kafka_messaging_interface import KafkaMessagingConsumer, KafkaMessagingProducer
import bot_logger


class Level:
    def __init__(self, budget, percentage, is_level_zero=False):
        self.budget = budget
        self.percentage = percentage
        self.is_level_zero = is_level_zero

        self.buy_executed = False
        self.buy_price = 0.0
        self.buy_qty = 0.0
        self.buy_executed_qty = 0.0

        self.sell_executed = False
        self.sell_price = 0.0
        self.sell_qty = 0.0
        self.sell_executed_qty = 0.0

        self.buy_order = None
        self.sell_order = None

        self.fill_ids = set()

    def reset(self):
        self.buy_executed = False
        self.buy_price = 0.0
        self.buy_qty = 0.0
        self.buy_executed_qty = 0.0

        self.sell_executed = False
        self.sell_price = 0.0
        self.sell_qty = 0.0
        self.sell_executed_qty = 0.0

        self.buy_order = None
        self.sell_order = None

        self.fill_ids = set()


class SymbolConfiguration:
    def __init__(self, symbol, level_zero_budget, budget_multiplier, sell_percentage,
                 percentage_qty_to_sell, levels):
        self.symbol = symbol
        self.level_zero_budget = level_zero_budget
        self.budget_multiplier = budget_multiplier
        self.sell_percentage = sell_percentage
        self.percentage_qty_to_sell = percentage_qty_to_sell

        self.level_zero = Level(self.level_zero_budget * self.budget_multiplier, self.sell_percentage, True)
        self.levels = []
        for level in levels:
            lvl = Level(float(level.USDBudget) * self.budget_multiplier, float(level.DownPercentage), False)
            self.levels.append(lvl)


class StrategyConfiguration:
    def __init__(self):
        pass


def get_price_for_crypto_in_usd(symbol):
    # redis details needed from Dan
    if symbol == "BTCUSDT":
        return 43005.91
    elif symbol == "BNBUSDT":
        return 493.0
    return None


def get_crypto_qty_from_ust_budget(symbol, usd_budget):
    price = get_price_for_crypto_in_usd(symbol)
    if not price:
        return None
    qty_to_buy = usd_budget / price
    return qty_to_buy


class StrategyClassPoll:
    def __init__(self, message, queue, parent_queue, exchange_interface_type, messaging_interface_type):
        self.message = message
        self.update_queue = queue
        self.parent_queue = parent_queue
        self.messaging_interface = messaging_interface_type()
        self.exchange_interface = exchange_interface_type(self.message, queue)
        self.symbol_configurations = {}

    def create_connection(self):
        # self.exchange_interface.
        pass

    def add_configuration_for_symbol(self, symbol, level_zero_budget, budget_multiplier, sell_percentage,
                                     percentage_qty_to_sell, levels):
        print(f" Parameters: {symbol}, {level_zero_budget}, {budget_multiplier}, {sell_percentage}"
              f", {percentage_qty_to_sell} \n {levels}")

        if symbol in self.symbol_configurations:
            print(f"Warning: symbol already exists: {symbol}")
            return False

        symbol_configuration = SymbolConfiguration(symbol, level_zero_budget, budget_multiplier, sell_percentage,
                                                   percentage_qty_to_sell, levels)

        self.symbol_configurations[symbol] = symbol_configuration
        return True

    def send_initial_orders_for_all_symbols(self):
        for symbol in self.symbol_configurations.keys():
            if not self.send_initial_orders_for_symbol(symbol):
                pass
        pass

    def refresh_bot_for_symbol(self, symbol):
        self.cancel_all_open_orders(symbol)
        self.send_initial_orders_for_symbol(symbol)

    def cancel_all_open_orders(self, symbol):
        self.exchange_interface.cancel_all()

    def get_quantity_to_sell(self, symbol_configuration, level, executed_qty, is_level_zero):
        return executed_qty

    def send_sell_on_buy_complete(self, symbol, level, side, executed_qty, executed_price, fill_id, is_level_zero):
        symbol_configuration = self.symbol_configurations.get(symbol)
        qty_to_sell = self.get_quantity_to_sell(symbol_configuration, level, executed_qty, is_level_zero)
        sell_price = executed_price * (1 + (symbol_configuration.sell_percentage / 100))

        rounded_qty_to_sell = round(qty_to_sell, self.exchange_interface.get_qty_precision(symbol))
        rounded_sell_price = round(sell_price, self.exchange_interface.get_price_precision(symbol))
        order = self.exchange_interface.send_order(symbol, SIDE_SELL, ORDER_TYPE_LIMIT,
                                                   TIME_IN_FORCE_GTC, rounded_qty_to_sell, rounded_sell_price)
        if not order:
            print(f"Error sending Sell order: {symbol}")
            return None

        return order

    def check_if_all_orders_compete(self, symbol):
        symbol_configuration = self.symbol_configurations.get(symbol)
        for level in symbol_configuration.levels:
            if not level.sell_executed:
                return False

        return True

    def refresh_if_all_sell_completed(self, symbol):
        if not self.check_if_all_orders_compete(symbol):
            return
        self.refresh_bot_for_symbol(symbol)

    def on_fill(self, symbol, level, side, executed_qty, executed_price, fill_id, is_level_zero):
        if fill_id in level.fill_ids:
            print(f"Fill id already processed {fill_id}")
            return True

        level.fill_ids.add(fill_id)

        if side == SIDE_BUY:
            level.buy_executed_qty += executed_qty
            if level.buy_executed_qty < level.buy_qty:
                print(f"partial fill {fill_id}")
                return True
        elif side == SIDE_SELL:
            level.sell_executed_qty += executed_qty
            if level.sell_executed_qty < level.sell_qty:
                print(f"partial fill {fill_id}")
                return True

        if is_level_zero:
            if side == SIDE_SELL:
                level.sell_executed = True
                self.refresh_bot_for_symbol(symbol)
            elif side == SIDE_BUY:
                self.send_sell_on_buy_complete(symbol, level, side, executed_qty, fill_id, is_level_zero)
        else:
            if side == SIDE_BUY:
                level.buy_executed = True
                self.send_sell_on_buy_complete(symbol, level, side, executed_qty, fill_id, is_level_zero)
            elif side == SIDE_SELL:
                level.sell_executed = True
                self.refresh_if_all_sell_completed(symbol)

    def send_initial_orders_for_symbol(self, symbol):
        symbol_configuration = self.symbol_configurations.get(symbol)
        symbol_configuration.level_zero.reset()

        qty_to_buy = get_crypto_qty_from_ust_budget(symbol, symbol_configuration.level_zero.budget)
        rounded_qty_to_buy = round(qty_to_buy, self.exchange_interface.get_qty_precision(symbol))

        print(f"qty_to_buy: {rounded_qty_to_buy} {qty_to_buy}")
        order = self.exchange_interface.send_mkt_order(symbol, SIDE_BUY, rounded_qty_to_buy)
        if not order:
            return False

        if order['status'] != 'FILLED' or 'fills' not in order or 0 == len(order['fills']):
            print(order)
            return False

        executed_price = float(order['fills'][0]['price'])
        executed_qty = float(order['fills'][0]['qty'])

        symbol_configuration.level_zero.buy_executed = True
        symbol_configuration.level_zero.buy_price = executed_price
        symbol_configuration.level_zero.buy_qty = rounded_qty_to_buy
        symbol_configuration.level_zero.buy_executed_qty = executed_qty
        symbol_configuration.level_zero.buy_order = order

        for level in symbol_configuration.levels:
            buy_price = executed_price * (1 - (level.percentage / 100))
            qty_to_buy = get_crypto_qty_from_ust_budget(symbol, level.budget)
            rounded_qty_to_buy = round(qty_to_buy, self.exchange_interface.get_qty_precision(symbol))
            rounded_buy_price = round(buy_price, self.exchange_interface.get_price_precision(symbol))
            order = self.exchange_interface.send_order(symbol, SIDE_BUY, ORDER_TYPE_LIMIT,
                                                       TIME_IN_FORCE_GTC, rounded_qty_to_buy, rounded_buy_price)
            if not order:
                print(f"Error sending Sell order: {symbol}")
                return False
            level.buy_qty = rounded_qty_to_buy
            level.buy_order = order

        return True

    def process_message(self, message_dict):
        print(f"Processing message: {message_dict['Type']} {self.parent_queue}")

    def bot_runner(self):
        self.create_connection()
        if not self.exchange_interface.initialized:
            print("Error running binance interface")
            return None

        print("starting order send...")
        for symbol_configuration in self.message.Configurations:
            ret = self.add_configuration_for_symbol(symbol_configuration.Configuration.Symbol,
                                                    float(symbol_configuration.Configuration.LevelZeroUSDBudget),
                                                    float(symbol_configuration.Configuration.BudgetMultiplier),
                                                    float(symbol_configuration.Configuration.SellPercentage),
                                                    float(symbol_configuration.Configuration.PercentQtyToSell),
                                                    symbol_configuration.Configuration.Levels)

            if not ret:
                return None

            print(symbol_configuration.Configuration.Symbol)

        self.send_initial_orders_for_all_symbols()
        while True:
            try:
                if not self.update_queue.empty():
                    msg = self.update_queue.get()
                    if isinstance(msg, dict):
                        self.process_message(msg)
                    else:
                        print("Not dictionary  ***********")
                else:
                    print("From bot process")
                    time.sleep(5)
            except Exception as e:
                print(f"Error occur in bot: {e}")


def bot_main(config, queue, parent_queue, exchange_interface_type, messaging_interface_type):
    print(f"Here 1")
    message = json.loads(config, object_hook=lambda d: SimpleNamespace(**d))
    strategy = StrategyClassPoll(message, queue, parent_queue, exchange_interface_type, messaging_interface_type)
    strategy.bot_runner()
