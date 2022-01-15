import unittest
import json
from pathlib import Path

from messaging.kafka_messaging_interface import KafkaMessagingProducer, KafkaMessagingConsumer, \
    DummpMessagingProducer, DummyMessagingConsumer

from bot.bot_controller import BotController
from bot.new_cryptobot_with_poll import BinancePollInterface
from exchanges.dummy_exchange_interface import DummyExchangeInterface

import threading
import time


class TestBotStart(unittest.TestCase):
    def test_bot_controller_start(self):
        configuration_update_topic = 'cumberland-30347.Configuration_Update'
        bot_update_topic = 'cumberland-30347.Bot_Updates'
    
        bot_controller = BotController(configuration_update_topic, bot_update_topic, DummyMessagingConsumer,
                                       DummpMessagingProducer, DummyExchangeInterface)

        message_consumer = bot_controller.message_consumer
        message_producer = bot_controller.message_producer
              
        x = threading.Thread(target=bot_controller.run_controller_loop)
        x.start()
        time.sleep(1)
        self.assertTrue(bot_controller.started)
        bot_controller.started = False

        time.sleep(5)
        x.join()
        time.sleep(2)
        self.assertTrue(not bot_controller.started)

    def test_bot_start(self):
        configuration_update_topic = 'cumberland-30347.Configuration_Update'
        bot_update_topic = 'cumberland-30347.Bot_Updates'
    
        bot_controller = BotController(configuration_update_topic, bot_update_topic, DummyMessagingConsumer,
                                       DummpMessagingProducer, DummyExchangeInterface)

        message_consumer = bot_controller.message_consumer
        message_producer = bot_controller.message_producer
              
        x = threading.Thread(target=bot_controller.run_controller_loop)
        x.start()
        time.sleep(1)
        self.assertTrue(bot_controller.started)

        txt = Path("StrategyConfigurationNew.json").read_text()
        message_consumer.message_to_send = txt

        time.sleep(10)
        bot_controller.started = False
        x.join()

    def test_bot_start_fills(self):
        configuration_update_topic = 'cumberland-30347.Configuration_Update'
        bot_update_topic = 'cumberland-30347.Bot_Updates'

        bot_controller = BotController(configuration_update_topic, bot_update_topic, DummyMessagingConsumer,
                                       DummpMessagingProducer, DummyExchangeInterface)

        message_consumer = bot_controller.message_consumer
        message_producer = bot_controller.message_producer

        x = threading.Thread(target=bot_controller.run_controller_loop)
        x.start()
        time.sleep(1)
        self.assertTrue(bot_controller.started)

        txt = Path("StrategyConfigurationNew.json").read_text()
        message_consumer.message_to_send = txt

        time.sleep(10)
        bot_controller.started = False
        x.join()


if __name__ == '__main__':
    unittest.main()
