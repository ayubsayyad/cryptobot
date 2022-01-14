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
from exchanges.binance_poll_interface import Binance_Poll_Interface
from messaging.kafka_messaging_interface import KafkaMessagingConsumer, KafkaMessagingProducer
import bot_logger


class SymbolConfiguration:
    def __init__(self, config_dictionary):

        pass
    pass


class StrategyConfiguration:
    def __init__(self):
        pass


class StrategyClassPoll:
    def __init__(self, message, queue, parent_queue, exchange_interface_type, messaging_interface_type):
        self.message = message
        self.update_queue = queue
        self.parent_queue = parent_queue
        self.messaging_interface = messaging_interface_type()
        self.exchange_interface = exchange_interface_type(self.message, queue)

    def create_connection(self):
        #self.exchange_interface.
        pass

    def send_initial_orders(self):
        pass

    def send_initial_orders_for_symbol(self, symbol):
        pass

    def process_message(self, message_dict):
        print(f"Processing message: {message_dict['Type']} {self.parent_queue}")

    def bot_runner(self):
        self.create_connection()
        if not self.exchange_interface.initialized:
            print("Error running binance interface")
            return None

        print("starting order send...")
        # self.cancel_all()
        # ret = self.send_orders_for_crypto()
        # if not ret:
        #     print("Bot failed to send initial orders, please check reason and restart")
        #     message = {"Type": "TerminateMe", "Client": self.message.clinet_details.Client_Id}
        #     self.parent_queue.put(message)
        #     return

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
