
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
import os
print(os.getenv('PYTHONPATH'))
from exchanges.binance_poll_interface import BinancePollInterface
from messaging.kafka_messaging_interface import KafkaMessagingConsumer, KafkaMessagingProducer
import bot_logger
import bot_with_oll


class BotController:
    def __init__(self, configuration_update_topic1, bot_update_topic1, message_consume_interface,
                 message_produce_interface, bot_exchange_interface) -> None:
        self.logger = bot_logger.get_logger("bot_controller")
        self.logger.info("starting Bot controller")
        self.parent_queue = multiprocessing.Queue()
        self.running_bots = {}
        self.bot_update_topic = bot_update_topic1

        self.message_consumer = message_consume_interface(configuration_update_topic1)
        self.message_producer = message_produce_interface()
        self.started = False

        self.bot_exchange_interface = bot_exchange_interface
        self.message_produce_interface = message_produce_interface

    def stop_all_running_bots(self):
        for key, val in list(self.running_bots.items()):
            self.logger.info(val)
            if val[0].is_alive():
                val[0].terminate()

        self.running_bots.clear()

    def send_message(self, json_string):
        self.message_producer.send(self.bot_update_topic, json_string)

    def update_bot_configuration(self, msg):
        message = json.loads(msg, object_hook=lambda d: SimpleNamespace(**d))
        if message.client_details.Client_Id not in self.running_bots:
            self.logger.warning("Bot not running")
            return False
        message_to_send = {'Type': "StrategyConfigurationUpdate", 'Value': msg}
        proc,  bot_queue = self.running_bots[message.client_details.Client_Id]
        bot_queue.put(message_to_send)

    def start_new_bot(self, msg):
        message = json.loads(msg, object_hook=lambda d: SimpleNamespace(**d))
        if message.client_details.Client_Id in self.running_bots:
            self.logger.warning("Bot already running")
            return False

        bot_queue = multiprocessing.Queue()
        print(f"starting new bot!!!! : {msg} \n")

        proc = Process(target=bot_with_oll.bot_main, args=(msg, bot_queue, self.parent_queue, self.bot_update_topic,
                                                           self.bot_exchange_interface, self.message_produce_interface))
        proc.start()
        self.running_bots[message.client_details.Client_Id] = (proc, bot_queue)
        return True

    def run_controller_loop(self):
        start_msg = {"Type": "BotControllerStarted"}
        self.send_message(json.dumps(start_msg, indent=2))
        self.started = True
        while self.started:
            try:
                if not self.parent_queue.empty():
                    msg = self.parent_queue.get()
                    if isinstance(msg, dict):
                        if msg["Type"] == "TerminateMe":
                            if msg["Client"] in self.running_bots:
                                proc, q = self.running_bots[msg["Client"]]
                                self.logger.warning("terminating process")
                                proc.terminate()
                                msg["Type"] = "ProcessTerminated"
                                json_string = json.dumps(msg, indent=2)
                                self.send_message(json_string)
                    else:
                        self.logger.warning("Not dictionary  ***********")

                else:
                    kafka_msg = self.message_consumer.poll(5)
                    if 0 != len(kafka_msg):
                        for topic, kafka_messages in kafka_msg.items():
                            for msg in kafka_messages:
                                json_data = json.loads(msg.value)
                                if json_data["Type"] == "StrategyConfigurationNew":
                                    if self.start_new_bot(msg.value):
                                        self.logger.warning("New bot started")
                                if json_data["Type"] == "StrategyConfigurationUpdate":
                                    if self.update_bot_configuration(msg.value):
                                        self.logger.warning("New bot started")

                                if json_data["Type"] == "StopTheBotController":
                                    self.logger.warning("Stopping Bot Controller")
                                    self.stop_all_running_bots()
                                    break
                    else:
                        self.logger.info("Running.")
                        for key, val in list(self.running_bots.items()):
                            self.logger.info(val)
                            if not val[0].is_alive():
                                res = self.running_bots.pop(key, None)
                                if res:
                                    self.logger.info(f"bot terminated, removed key: {key}")

                        time.sleep(5)
            except Exception as e:
                self.logger.warning(f"Error occur in controller: {e}")

        print("STOPPING .....")
        self.stop_all_running_bots()
        self.started = False


if __name__ == "__main__":
    configuration_update_topic = 'cumberland-30347.Configuration_Update'
    bot_update_topic = 'cumberland-30347.Bot_Updates'

    bot_controller = BotController(configuration_update_topic, bot_update_topic, KafkaMessagingConsumer,
                                   KafkaMessagingProducer, BinancePollInterface)
    bot_controller.run_controller_loop()
