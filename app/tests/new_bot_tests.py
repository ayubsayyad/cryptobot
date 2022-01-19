import multiprocessing
import unittest
import json
from pathlib import Path
from types import SimpleNamespace

from messaging.kafka_messaging_interface import KafkaMessagingProducer, KafkaMessagingConsumer, \
    DummpMessagingProducer, DummyMessagingConsumer

from bot.bot_controller import BotController
from bot.bot_with_oll import StrategyClassPoll
from bot.new_cryptobot_with_poll import BinancePollInterface
from exchanges.dummy_exchange_interface import DummyExchangeInterface

import threading
import time


class TestBotStart(unittest.TestCase):
    def test_bot_initialization(self):
        txt = Path("StrategyConfigurationNew.json").read_text()
        message = json.loads(txt, object_hook=lambda d: SimpleNamespace(**d))
        queue = multiprocessing.Queue()
        parent_queue = multiprocessing.Queue()
        strategy = StrategyClassPoll(message, queue, parent_queue, "", DummyExchangeInterface, DummpMessagingProducer)
        ret = strategy.initialize_bot()
        self.assertTrue(ret)

    def test_bot_onfill_for_level_zero(self):
        txt = Path("StrategyConfigurationNew_one.json").read_text()
        message = json.loads(txt, object_hook=lambda d: SimpleNamespace(**d))
        queue = multiprocessing.Queue()
        parent_queue = multiprocessing.Queue()
        strategy = StrategyClassPoll(message, queue, parent_queue, "", DummyExchangeInterface, DummpMessagingProducer)
        ret = strategy.initialize_bot()
        self.assertTrue(ret)

        print(strategy.exchange_interface.last_mkt_order)
        self.assertTrue(strategy.exchange_interface.last_mkt_order['symbol'] == 'BTCUSDT')
        print(strategy.exchange_interface.last_orders)
        print("Sending update______________________")
        txt = Path("StrategyConfigurationUpdate.json").read_text()
        print(txt)
        message_to_send = {'Type': "StrategyConfigurationUpdate", 'Value': txt}
        self.assertTrue(strategy.process_message(message_to_send))


if __name__ == '__main__':
    unittest.main()
