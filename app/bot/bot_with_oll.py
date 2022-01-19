import asyncio
import copy
import json
import multiprocessing
import os
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
import redis


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

        self.processed_fill_ids = set()

        self.level_zero = Level(self.level_zero_budget * self.budget_multiplier, self.sell_percentage, True)
        self.levels = []
        for level in levels:
            lvl = Level(float(level.USDBudget) * self.budget_multiplier, float(level.DownPercentage), False)
            self.levels.append(lvl)


class StrategyConfiguration:
    def __init__(self):
        pass


class StrategyClassPoll:
    def __init__(self, message, queue, parent_queue, bot_update_topic, exchange_interface_type,
                 messaging_interface_type):
        self.message = message
        self.update_queue = queue
        self.parent_queue = parent_queue
        self.bot_update_topic = bot_update_topic
        self.messaging_interface = messaging_interface_type()
        self.exchange_interface = exchange_interface_type(self.message, queue)
        self.symbol_configurations = {}
        self.redis_conn = redis_conn = redis.from_url(os.getenv('REDIS_URL'))

    def create_connection(self):
        # self.exchange_interface.
        self.exchange_interface.create()
        pass

    def get_price_for_crypto_in_usd(self, symbol):
        # redis details needed from Dan
        if self.redis_conn:
            price = self.redis_conn.get(symbol)
            if price:
                print(f'price from redis: {price}')
                return float(price)

        if symbol == "BTCUSDT":
            return 43005.91
        elif symbol == "BNBUSDT":
            return 493.0
        elif symbol == "MATICUSDT":
            return 2.290
        return None

    def get_crypto_qty_from_ust_budget(self, symbol, usd_budget):
        price = self.get_price_for_crypto_in_usd(symbol)
        if not price:
            return None
        qty_to_buy = usd_budget / price
        return qty_to_buy

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
                return False

        return True

    def refresh_bot_for_symbol(self, symbol):
        self.cancel_all_open_orders(symbol)
        self.send_initial_orders_for_symbol(symbol)

    def cancel_all_open_orders(self, symbol):
        self.exchange_interface.cancel_all(symbol)

    def get_quantity_to_sell(self, symbol_configuration, level, executed_qty, is_level_zero):
        return executed_qty

    def send_sell_on_buy_complete(self, symbol, level, side, executed_qty, executed_price, is_level_zero):
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

        level.sell_order = order
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

    def on_fill(self, symbol, level, side, executed_qty, executed_price, is_level_zero):
        print(f"on fill: {symbol}, {level}, {side}, {executed_qty}, {executed_price}, {is_level_zero}")
        if side == SIDE_BUY:
            level.buy_executed_qty += executed_qty
            print(f"on fill buy: {executed_qty} {level.buy_executed_qty}")
        elif side == SIDE_SELL:
            print(f"on fill sell {executed_qty}")
            level.sell_executed_qty += executed_qty

        if is_level_zero:
            if side == SIDE_SELL:
                print(f"level zero sell executed : {level.sell_executed_qty} at {executed_price}")
                level.sell_executed = True
                self.refresh_bot_for_symbol(symbol)
            elif side == SIDE_BUY:
                print(f"level zero buy executed : {level.buy_executed_qty} at {executed_price}")
                self.send_sell_on_buy_complete(symbol, level, side, executed_qty, executed_price, is_level_zero)
        else:
            if side == SIDE_BUY:
                level.buy_executed = True
                self.send_sell_on_buy_complete(symbol, level, side, executed_qty, executed_price, is_level_zero)
            elif side == SIDE_SELL:
                level.sell_executed = True
                self.refresh_if_all_sell_completed(symbol)

    def send_initial_orders_for_symbol(self, symbol):
        symbol_configuration = self.symbol_configurations.get(symbol)
        symbol_configuration.level_zero.reset()

        qty_to_buy = self.get_crypto_qty_from_ust_budget(symbol, symbol_configuration.level_zero.budget)
        rounded_qty_to_buy = round(qty_to_buy, self.exchange_interface.get_qty_precision(symbol))

        print(f"qty_to_buy: {rounded_qty_to_buy}")
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
        symbol_configuration.level_zero.buy_order = order

        for level in symbol_configuration.levels:
            buy_price = executed_price * (1 - (level.percentage / 100))
            qty_to_buy = self.get_crypto_qty_from_ust_budget(symbol, level.budget)
            rounded_qty_to_buy = round(qty_to_buy, self.exchange_interface.get_qty_precision(symbol))
            rounded_buy_price = round(buy_price, self.exchange_interface.get_price_precision(symbol))
            order = self.exchange_interface.send_order(symbol, SIDE_BUY, ORDER_TYPE_LIMIT,
                                                       TIME_IN_FORCE_GTC, rounded_qty_to_buy, rounded_buy_price)
            if not order:
                print(f"Error sending Sell order: {symbol}")
                return False
            level.buy_qty = rounded_qty_to_buy
            level.buy_order = order

        # process the fill for first order as its executed as market order
        self.on_fill(symbol, symbol_configuration.level_zero, SIDE_BUY, executed_qty, executed_price, True)

        return True

    def poll_for_fills(self):
        for symbol, symbol_configuration in self.symbol_configurations.items():
            if symbol_configuration.level_zero.sell_order and not symbol_configuration.level_zero.sell_executed:
                order_id = int(symbol_configuration.level_zero.sell_order["orderId"])
                order = self.exchange_interface.get_client_order(symbol, order_id)
                print(f" Level zero Order : {order}")
                if order and order['status'] == 'FILLED':
                    self.on_fill(symbol, symbol_configuration.level_zero, SIDE_SELL, float(order["executedQty"]),
                                 float(order["price"]), True)
                    # this will refresh bot as per our logic to refresh if sell of level zero is executed
                    break
            for level in symbol_configuration.levels:
                if level.sell_order and not level.sell_executed:
                    order_id = int(level.sell_order["orderId"])
                    order = self.exchange_interface.get_client_order(symbol, order_id)
                    print(f" Level  Order Sell : {order}")
                    if order and order['status'] == 'FILLED':
                        self.on_fill(symbol, symbol_configuration.level_zero, SIDE_SELL,
                                     float(order["executedQty"]), float(order["price"]), False)

                if level.buy_order and not level.buy_executed:
                    order_id = int(level.buy_order["orderId"])
                    order = self.exchange_interface.get_client_order(symbol, order_id)
                    print(f" Level  Order buy : {order}")
                    if order and order['status'] == 'FILLED':
                        self.on_fill(symbol, symbol_configuration.level_zero, SIDE_BUY,
                                     float(order["executedQty"]), float(order["price"]), False)

    def process_strategy_config_update(self, message_dict):
        if message_dict['Type'] == 'StrategyConfigurationUpdate':
            value = message_dict['Value']
            message_update = json.loads(value, object_hook=lambda d: SimpleNamespace(**d))
            for symbol_configuration in message_update.Configurations:
                if symbol_configuration.Configuration.Symbol in self.symbol_configurations:
                    print(f"Error Configuration for symbol already exists: {symbol_configuration.Configuration.Symbol}")
                    return False

            for symbol_configuration in message_update.Configurations:
                ret = self.add_configuration_for_symbol(symbol_configuration.Configuration.Symbol,
                                                        float(symbol_configuration.Configuration.LevelZeroUSDBudget),
                                                        float(symbol_configuration.Configuration.BudgetMultiplier),
                                                        float(symbol_configuration.Configuration.SellPercentage),
                                                        float(symbol_configuration.Configuration.PercentQtyToSell),
                                                        symbol_configuration.Configuration.Levels)

                if not ret:
                    return False

                print(symbol_configuration.Configuration.Symbol)

            for symbol_configuration in message_update.Configurations:
                if not self.send_initial_orders_for_symbol(symbol_configuration.Configuration.Symbol):
                    return False

    def process_exchange_response_account(self, message_dict):
        json_string = json.dumps(message_dict, indent=2)
        self.self.messaging_interface.send(self.bot_update_topic, json_string)

    def process_error_message(self, message_dict):
        json_string = json.dumps(message_dict, indent=2)
        self.self.messaging_interface.send(self.bot_update_topic, json_string)

    def process_account_message(self, message_dict):
        json_string = json.dumps(message_dict, indent=2)
        print(json_string)
        self.self.messaging_interface.send(self.bot_update_topic, json_string)

    def process_message(self, message_dict):
        print(message_dict)
        if message_dict['Type'] == 'StrategyConfigurationUpdate':
            self.process_strategy_config_update(message_dict)
        elif message_dict['Type'] == 'ExchangeResponseAccount':
            self.process_exchange_response_account(message_dict)
        elif message_dict['Type'] == 'BinanceErrorOccurred':
            self.process_error_message(message_dict)
        elif message_dict['Type'] == 'ExchangeResponseAccount':
            self.process_account_message(message_dict)

        print(f"Processing message: {message_dict['Type']} {self.parent_queue}")
        return True

    def initialize_bot(self):
        self.create_connection()
        if not self.exchange_interface.initialized:
            print("Error running binance interface")
            return False

        print("starting order send...")
        for symbol_configuration in self.message.Configurations:
            ret = self.add_configuration_for_symbol(symbol_configuration.Configuration.Symbol,
                                                    float(symbol_configuration.Configuration.LevelZeroUSDBudget),
                                                    float(symbol_configuration.Configuration.BudgetMultiplier),
                                                    float(symbol_configuration.Configuration.SellPercentage),
                                                    float(symbol_configuration.Configuration.PercentQtyToSell),
                                                    symbol_configuration.Configuration.Levels)

            if not ret:
                return False

            print(symbol_configuration.Configuration.Symbol)

        print(f"send initial orders")
        return self.send_initial_orders_for_all_symbols()

    def bot_runner(self):
        if not self.initialize_bot():
            print(f"bot initialization failed, will terminate")
            return False

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
                    self.poll_for_fills()
                    time.sleep(5)
            except Exception as e:
                print(f"Error occur in bot: {e}")


def bot_main(config, queue, parent_queue, bot_update_topic, exchange_interface_type, messaging_interface_type):
    print(f"Here 1")
    message = json.loads(config, object_hook=lambda d: SimpleNamespace(**d))
    strategy = StrategyClassPoll(message, queue, parent_queue, bot_update_topic, exchange_interface_type,
                                 messaging_interface_type)
    strategy.bot_runner()
