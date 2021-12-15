#import 
import json
import sys
import time
import logging
import copy
import yaml
from argparse import ArgumentParser
from strategies.strategyfactory import StrategyFactory
from strategies.istrategyinterface import IStrategyInterface
from confluent_kafka import Producer, Consumer, KafkaError
from messages.python.strategyconfigmessage import StrategyConfigMessage


class CryptoBot:
    def __init__(self, name) -> None:
        pass

    def run_bot_function():
        pass

class CryptoBotController:
    def __init__(self, args) -> None:
        print("Bot controller created")
        self.running_bots = {}
        self.yaml_conf = args.yaml_conf
        self.is_fresh = args.is_fresh
        self.kafka_consumer = None
        self.kafka_controller_topics = []
        self.kafka_settings = None
        print(self.is_fresh)

    def init_bot_control(self):
        with open(self.yaml_conf, "r") as f:
            config = yaml.safe_load(f)
            self.kafka_settings = config['kafka']
            self.kafka_controller_topics = config['kafka.controller.topics']
            print(self.kafka_controller_topics)
            self.kafka_consumer = Consumer(self.kafka_settings)
            self.kafka_consumer.subscribe(self.kafka_controller_topics)


    def bot_runner_function(self, message, strategy):
        print("bot_runner_function:" + str(message) + str(strategy))
        print(self.kafka_settings)
        bot_settings = copy.deepcopy(self.kafka_settings)
        bot_settings['group.id'] = bot_settings['group.id'] + "."+message.client_id
        kafka_bot_consumer = Consumer(bot_settings)
        topics = [message.market_data_topic, message.config_update_topic, message.kafka_topic_admin]
        kafka_bot_consumer.subscribe(self.kafka_controller_topics)
        while (True):
            try:
                msg = kafka_bot_consumer.poll(1)
                if msg:
                    print("bot_runner_function" + str(msg))
            except Exception as e:
                print(e)


    def handle_strategy_configuration(self, jsondata):
        message = StrategyConfigMessage(jsondata)
        if message.client_id in self.running_bots:
            print("bot is already running id:" + message.client_id)
            return None

        factory = StrategyFactory()
        strategy  = factory.create_strategy(message.strategy_plugin)
        if strategy is None:
            print("invalid strategy plugin" + message.strategy_plugin)
            return None

        print("create strategy with plugin:" + message.strategy_plugin)
        proc = Process(target = self.bot_runner_function, args=(message, strategy))
        proc.start()
        self.running_bots[message.client_id] = proc

    def handle_kafka_message(self, msg):
        jsondata = json.loads(msg.value())
        print(jsondata["Type"])
        if jsondata["Type"] == "StrategyConfiguration":
            self.handle_strategy_configuration(jsondata)
        pass

    def run_bot_control(self):
        try:
            while (True):
                try:
                    msg = self.kafka_consumer.poll(1)
                    if msg:
                        self.handle_kafka_message(msg)
                except Exception as e:
                    print(e)
                    #print(traceback.format_exc())
        except KeyboardInterrupt:
            pass

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("-c", "--config", dest="yaml_conf")
    parser.add_argument("-f", "--is fresh start", dest="is_fresh", default=True)
    args = parser.parse_args()
    bot = CryptoBotController(args)
    bot.init_bot_control()
    bot.run_bot_control() 
