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
    def __init__(self, qty_to_trade, percentage, qty_unit, is_level_zero=False):
        self.qty_to_trade = qty_to_trade * qty_unit
        self.percentage = percentage
        self.buy_executed = False
        self.sell_executed = False
        self.buy_order = None
        self.sell_order = None
        self.is_level_zero = is_level_zero


class CryptoLevel:
    def __init__(self, conf):
        self.crypto = conf.Configuration.Crypto
        self.level_0_qty = float(conf.Configuration.Level0Qty)
        qty_unit = float(conf.Configuration.QtyUnit)
        self.sell_percent = float(conf.Configuration.SellPercent)
        self.level_zero = None
        self.first_order = None
        self.buy_executed = False

        self.level_zero = Level(self.level_0_qty, 0, qty_unit, True)

        self.levels = []
        for level in conf.Configuration.levels:
            qty_to_trade = float(level.Qty) * qty_unit
            percentage = float(level.Percentage)
            lvl = Level(qty_to_trade, percentage, qty_unit, False)
            self.levels.append(lvl)


class StrategyClassPoll:
    def __init__(self, message, queue, parent_queue, exchange_interface, messaging_interface):
        self.exchange_interface = exchange_interface
        self.message = message
        self.iface = None
        self.kafka_producer = messaging_interface()
        self.queue = queue
        self.parent_queue = parent_queue
        self.crypto_levels = {}
        for conf in self.message.Configurations:
            crypto = conf.Configuration.Crypto
            cryptolvl = CryptoLevel(conf)
            self.crypto_levels[crypto] = cryptolvl

    def create_connection(self):
        self.iface.create()

    def cancel_all(self):
        self.iface.cancel_all()

    def send_orders_for_crypto(self):
        for crypto, conf in self.crypto_levels.items():
            print(f"\nsending orders for: {crypto}\n")
            ret = self.send_orders(crypto, conf)
            if not ret:
                print(f"\n failed sending orders for: {crypto}\n")
                self.cancel_all()
                return False

        return True

    def send_orders(self, crypto, conf):
        # derive initial price with first market order
        first_order = self.iface.send_mkt_order(crypto, SIDE_BUY, conf.level_zero.qty_to_trade)
        print(f'first_order: {first_order}')
        if not first_order:
            return False

        if 0 == len(first_order['fills']):
            return False

        conf.level_zero.buy_order = first_order

        trades = self.iface.get_client_trades(crypto)
        print(trades)

        initial_price = float(first_order['fills'][0]['price'])

        for level in conf.levels:
            price_to_send = initial_price * (1 - (level.percentage / 100))
            order = self.send_order(crypto, SIDE_BUY, level.qty_to_trade, price_to_send)
            if order is not None:
                level.buy_order = order
                print(f'level orders:{order}')
            else:
                print("Error sending order")
                return False

        return True

    def send_order(self, symbol, side, qty, price):
        order = self.iface.send_order(symbol, side, ORDER_TYPE_LIMIT, TIME_IN_FORCE_GTC, qty, price)
        # copied_order = copy.deepcopy(order)
        # copied_order[""]
        return order

    def send_sell_order(self, crypto_level, level, symbol, executedQty, price):
        qty = max(level.qty_to_trade, executedQty)
        sell_price = price * (1 + (crypto_level.sell_percent / 100))
        order = self.send_order(symbol, SIDE_SELL, qty, sell_price)
        level.sell_order = order
        print(f"sell order sent at price: {sell_price}")

    def send_message_to_kafka(self, json_string):
        future = self.kafka_producer.send('cumberland-30347.Bot_Updates', json_string)
        self.kafka_producer.flush()
        print("sent on kafka: cumberland-30347.Bot_Updates")

    def on_account_info(self, message):
        print(message)
        json_string = json.dumps(message, indent=2)
        self.send_message_to_kafka(json_string)

    def on_error(self, message):
        json_string = json.dumps(message, indent=2)
        self.send_message_to_kafka(json_string)
        pass

    def on_execution_report(self, message):
        print("on_execution_report")
        symbol = message["s"]
        order_id = int(message["i"])
        # order = self.iface.get_order(symbol, order_id)
        # print(f'**************************** {order}')

    def get_level(self, symbol, orderId, side):
        ret = self.crypto_levels.get(symbol)
        if None == ret:
            return None, None

        # if ret.first_order and self.first_order
        if (side == 'BUY' and ret.level_zero.buy_order is not None) and (
                orderId == int(ret.level_zero.buy_order['orderId'])):
            print("Level ZERO ***************************** BUY")
            return ret, ret.level_zero

        elif (side == 'SELL' and ret.level_zero.sell_order is not None) and (
                orderId == int(ret.level_zero.sell_order['orderId'])):
            print("Level ZERO ***************************** SELL")
            return ret, ret.level_zero

        for level in ret.levels:
            if (side == 'BUY' and level.buy_order is not None) and (orderId == int(level.buy_order['orderId'])):
                return ret, level
            else:
                if level.sell_order is not None and orderId == int(level.sell_order['orderId']):
                    return ret, level
        return None, None

    def refresh_bot(self, symbol, crypto_level):
        for level in crypto_level.levels:
            level.sell_executed = False
            level.buy_executed = False
            level.sell_order = None
            level.buy_order = None

        self.send_orders(symbol, crypto_level)

    def if_all_orders_complete_refresh(self, symbol, crypto_level):
        if crypto_level.level_zero.sell_executed and crypto_level.level_zero.buy_executed:
            pass
        else:
            return False

        for level in crypto_level.levels:
            if level.sell_executed and level.buy_executed:
                pass
            else:
                return False

        print("*************************** if_all_orders_complete_refersh ******************************")
        self.refresh_bot(self, symbol, crypto_level)

    def on_fill(self, message):
        print(f"on fill: {message}")
        price = float(message['price'])
        last_price = float(message['LastExcutionPrice'])
        if price == 0.0:
            price = last_price

        executed_qty = float(message['executedQty'])
        symbol = message['symbol']
        side = message['side']
        order_id = int(message['orderId'])
        crypto_level, level = self.get_level(symbol, order_id, side)
        if not level:
            print("Error could not get order")

        if side == 'BUY':
            if not level.buy_executed:
                level.buy_executed = True
                self.send_sell_order(crypto_level, level, symbol, executed_qty, price)
        else:
            if not level.sell_executed:
                level.sell_executed = True
                if level.is_level_zero:
                    self.cancel_all()
                    self.refresh_bot(symbol, crypto_level)

    def on_order_status(self, message):
        print(f"on_order_status: {message}")
        json_string = json.dumps(message, indent=2)
        self.send_message_to_kafka(json_string)

        if message["CurrentStatus"] == "FILLED" and message["status"] == "FILLED":
            self.on_fill(message)

    def on_exchange_response(self, message):
        print(message)
        json_string = json.dumps(message, indent=2)
        self.send_message_to_kafka(json_string)

    def on_add_new_crypto(self, message):
        pass

    def process_message(self, message):
        if "Type" not in message:
            print(f"Invalid message: {message}")
            return

        if message["Type"] == "ExchangeResponseAccount":
            self.on_exchange_response(message)
        elif message["Type"] == "BalanceExchangeResponse":
            self.on_exchange_response(message)
        elif message["Type"] == "ExecutionReport":
            self.on_execution_report(message)
        elif message["Type"] == "BinanceErrorOccurred":
            print(f"binance error: {message}")
            self.on_exchange_response(message)
        elif message["Type"] == "OrderStatus":
            self.on_order_status(message)
        elif message["Type"] == "AddNewCrypto":
            self.on_add_new_crypto(message)
        else:
            print("Message type not handled")

    def bot_runner(self):
        iface = self.exchange_interface(self.message, self.queue)
        self.set_iface(iface)
        self.create_connection()
        if not self.iface.initialized:
            print("Error running binance interface")
            return None

        print("starting order send...")
        self.cancel_all()
        ret = self.send_orders_for_crypto()
        if not ret:
            print("Bot failed to send initial orders, please check reason and restart")
            message = {"Type": "TerminateMe", "Client": self.message.client_details.Client_Id}
            self.parent_queue.put(message)
            return

        while True:
            try:
                if not self.queue.empty():
                    msg = self.queue.get()
                    if isinstance(msg, dict):
                        self.process_message(msg)
                    else:
                        print("Not dictionary  ***********")
                else:
                    time.sleep(5)
            except Exception as e:
                print(f"Error occur in bot: {e}")


def bot_main(config, queue, parent_queue, exchange_interface, messaging_interface):
    # f = open(config,)
    message = json.loads(config, object_hook=lambda d: SimpleNamespace(**d))
    strategy = StrategyClassPoll(message, queue, parent_queue, exchange_interface, messaging_interface)
    strategy.bot_runner()

# ###################################################################################################
# ##########################################################
