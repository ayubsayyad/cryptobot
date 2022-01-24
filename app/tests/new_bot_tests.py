import multiprocessing
import unittest
import json
from pathlib import Path
from types import SimpleNamespace
import copy
from messaging.kafka_messaging_interface import KafkaMessagingProducer, KafkaMessagingConsumer, \
    DummpMessagingProducer, DummyMessagingConsumer

from bot.bot_controller import BotController
from bot.bot_with_oll import StrategyClassPoll
from bot.new_cryptobot_with_poll import BinancePollInterface
from exchanges.dummy_exchange_interface import DummyExchangeInterface
from messaging.dummy_redis_interface import DummyRedisInterface
import threading
import time


class TestBotStart(unittest.TestCase):
    def test_bot_initialization(self):
        txt = Path("StrategyConfigurationNew.json").read_text()
        message = json.loads(txt, object_hook=lambda d: SimpleNamespace(**d))
        queue = multiprocessing.Queue()
        parent_queue = multiprocessing.Queue()
        strategy = StrategyClassPoll(message, queue, parent_queue, "", DummyExchangeInterface, DummpMessagingProducer,
                                     DummyRedisInterface)
        ret = strategy.initialize_bot()
        self.assertTrue(ret)

    def test_bot_send_initial_orders(self):
        txt = Path("StrategyConfigurationNew_one.json").read_text()
        message = json.loads(txt, object_hook=lambda d: SimpleNamespace(**d))
        queue = multiprocessing.Queue()
        parent_queue = multiprocessing.Queue()
        strategy = StrategyClassPoll(message, queue, parent_queue, "", DummyExchangeInterface, DummpMessagingProducer,
                                     DummyRedisInterface)
        ret = strategy.initialize_bot()
        self.assertTrue(ret)
        self.assertTrue(strategy.exchange_interface.last_mkt_order['symbol'] == 'BTCUSDT')

    def test_bot_onfill_for_level_zero(self):
        txt = Path("StrategyConfigurationNew_one.json").read_text()
        message = json.loads(txt, object_hook=lambda d: SimpleNamespace(**d))
        queue = multiprocessing.Queue()
        parent_queue = multiprocessing.Queue()
        strategy = StrategyClassPoll(message, queue, parent_queue, "", DummyExchangeInterface, DummpMessagingProducer,
                                     DummyRedisInterface)
        ret = strategy.initialize_bot()
        self.assertTrue(ret)

        # print(strategy.exchange_interface.last_mkt_order)
        self.assertTrue(strategy.exchange_interface.last_mkt_order['symbol'] == 'BTCUSDT')
        # print(f" Price: {strategy.get_price_for_crypto_in_usd('BTCUSDT')}")
        # print(f"Lastorders1: {strategy.exchange_interface.last_orders}")
        self.assertTrue(len(strategy.exchange_interface.last_orders) == 3)

    def test_bot_validate_sent_order_price(self):
        txt = Path("StrategyConfigurationNew_one.json").read_text()
        message = json.loads(txt, object_hook=lambda d: SimpleNamespace(**d))
        queue = multiprocessing.Queue()
        parent_queue = multiprocessing.Queue()
        strategy = StrategyClassPoll(message, queue, parent_queue, "", DummyExchangeInterface, DummpMessagingProducer,
                                     DummyRedisInterface)
        ret = strategy.initialize_bot()
        self.assertTrue(ret)

        # print(strategy.exchange_interface.last_mkt_order)
        self.assertTrue(strategy.exchange_interface.last_mkt_order['symbol'] == 'BTCUSDT')
        # print(f" Price: {strategy.get_price_for_crypto_in_usd('BTCUSDT')}")
        # print(f"Lastorders1: {strategy.exchange_interface.last_orders}")
        self.assertTrue(len(strategy.exchange_interface.last_orders) == 3)

        level_zero_budget = float(message.Configurations[0].Configuration.LevelZeroUSDBudget)
        budget_multiplier = float(message.Configurations[0].Configuration.BudgetMultiplier)
        symbol_price = strategy.get_price_for_crypto_in_usd('BTCUSDT')

        expected_sell_qty = (level_zero_budget * budget_multiplier) / symbol_price
        expected_sell_qty = round(expected_sell_qty, strategy.exchange_interface.get_qty_precision('BTCUSDT'))
        # print(expected_sell_qty)

        # check last mkt order qty is proper
        self.assertTrue(strategy.exchange_interface.last_mkt_order['symbol'] == 'BTCUSDT')
        self.assertTrue(expected_sell_qty == float(strategy.exchange_interface.last_orders[2]['origQty']))

        # now check buy orders
        ltp = float(strategy.exchange_interface.last_mkt_order['fills'][0]['price'])
        expected_buy_price = ltp * (1 - (float(message.Configurations[0].Configuration.Levels[0].DownPercentage) / 100))
        self.assertTrue(expected_buy_price == float(strategy.exchange_interface.last_orders[0]['price']))

        expected_buy_price = ltp * (1 - (float(message.Configurations[0].Configuration.Levels[1].DownPercentage) / 100))
        self.assertTrue(expected_buy_price == float(strategy.exchange_interface.last_orders[1]['price']))

    def test_bot_validate_new_crypto_add(self):
        txt = Path("StrategyConfigurationNew_one.json").read_text()
        message = json.loads(txt, object_hook=lambda d: SimpleNamespace(**d))
        queue = multiprocessing.Queue()
        parent_queue = multiprocessing.Queue()
        strategy = StrategyClassPoll(message, queue, parent_queue, "", DummyExchangeInterface, DummpMessagingProducer,
                                     DummyRedisInterface)
        ret = strategy.initialize_bot()
        self.assertTrue(ret)

        # print(strategy.exchange_interface.last_mkt_order)
        self.assertTrue(strategy.exchange_interface.last_mkt_order['symbol'] == 'BTCUSDT')
        # print(f" Price: {strategy.get_price_for_crypto_in_usd('BTCUSDT')}")
        # print(f"Lastorders1: {strategy.exchange_interface.last_orders}")
        self.assertTrue(len(strategy.exchange_interface.last_orders) == 3)

        level_zero_budget = float(message.Configurations[0].Configuration.LevelZeroUSDBudget)
        budget_multiplier = float(message.Configurations[0].Configuration.BudgetMultiplier)
        symbol_price = strategy.get_price_for_crypto_in_usd('BTCUSDT')

        expected_sell_qty = (level_zero_budget * budget_multiplier) / symbol_price
        expected_sell_qty = round(expected_sell_qty, strategy.exchange_interface.get_qty_precision('BTCUSDT'))
        # print(expected_sell_qty)

        # check last mkt order qty is proper
        self.assertTrue(strategy.exchange_interface.last_mkt_order['symbol'] == 'BTCUSDT')
        self.assertTrue(expected_sell_qty == float(strategy.exchange_interface.last_orders[2]['origQty']))

        # now check buy orders
        ltp = float(strategy.exchange_interface.last_mkt_order['fills'][0]['price'])
        expected_buy_price = ltp * (1 - (float(message.Configurations[0].Configuration.Levels[0].DownPercentage) / 100))
        self.assertTrue(expected_buy_price == float(strategy.exchange_interface.last_orders[0]['price']))

        expected_buy_price = ltp * (1 - (float(message.Configurations[0].Configuration.Levels[1].DownPercentage) / 100))
        self.assertTrue(expected_buy_price == float(strategy.exchange_interface.last_orders[1]['price']))

        strategy.exchange_interface.last_mkt_order = None
        strategy.exchange_interface.last_orders.clear()
        # print("Sending update______________________")
        txt = Path("StrategyConfigurationUpdate.json").read_text()
        # print(txt)
        message_to_send = {'Type': "StrategyConfigurationUpdate", 'Value': txt}
        self.assertTrue(strategy.process_message(message_to_send))

        message = json.loads(txt, object_hook=lambda d: SimpleNamespace(**d))

        self.assertTrue(strategy.exchange_interface.last_mkt_order['symbol'] == 'MATICUSDT')
        self.assertTrue(len(strategy.exchange_interface.last_orders) == 3)
        # print(f"Lastorders2: {strategy.exchange_interface.last_orders}")

        level_zero_budget = float(message.Configurations[0].Configuration.LevelZeroUSDBudget)
        budget_multiplier = float(message.Configurations[0].Configuration.BudgetMultiplier)
        symbol_price = strategy.get_price_for_crypto_in_usd('MATICUSDT')

        expected_sell_qty = (level_zero_budget * budget_multiplier) / symbol_price
        expected_sell_qty = round(expected_sell_qty, strategy.exchange_interface.get_qty_precision('MATICUSDT'))
        # print(expected_sell_qty)

        # check last mkt order qty is proper
        self.assertTrue(strategy.exchange_interface.last_mkt_order['symbol'] == 'MATICUSDT')
        self.assertTrue(expected_sell_qty == float(strategy.exchange_interface.last_orders[2]['origQty']))

        # now check buy orders
        ltp = float(strategy.exchange_interface.last_mkt_order['fills'][0]['price'])
        expected_buy_price = ltp * (1 - (float(message.Configurations[0].Configuration.Levels[0].DownPercentage) / 100))
        self.assertTrue(expected_buy_price == float(strategy.exchange_interface.last_orders[0]['price']))

        expected_buy_price = ltp * (1 - (float(message.Configurations[0].Configuration.Levels[1].DownPercentage) / 100))
        self.assertTrue(expected_buy_price == float(strategy.exchange_interface.last_orders[1]['price']))

    def test_buy_execution(self):
        txt = Path("StrategyConfigurationNew_one.json").read_text()
        message = json.loads(txt, object_hook=lambda d: SimpleNamespace(**d))
        queue = multiprocessing.Queue()
        parent_queue = multiprocessing.Queue()
        strategy = StrategyClassPoll(message, queue, parent_queue, "", DummyExchangeInterface, DummpMessagingProducer,
                                     DummyRedisInterface)
        ret = strategy.initialize_bot()
        self.assertTrue(ret)

        # print(strategy.exchange_interface.last_mkt_order)
        self.assertTrue(strategy.exchange_interface.last_mkt_order['symbol'] == 'BTCUSDT')
        # print(f" Price: {strategy.get_price_for_crypto_in_usd('BTCUSDT')}")
        # print(f"Lastorders1: {strategy.exchange_interface.last_orders}")
        self.assertTrue(len(strategy.exchange_interface.last_orders) == 3)

        level_zero_budget = float(message.Configurations[0].Configuration.LevelZeroUSDBudget)
        budget_multiplier = float(message.Configurations[0].Configuration.BudgetMultiplier)
        symbol_price = strategy.get_price_for_crypto_in_usd('BTCUSDT')

        expected_sell_qty = (level_zero_budget * budget_multiplier) / symbol_price
        expected_sell_qty = round(expected_sell_qty, strategy.exchange_interface.get_qty_precision('BTCUSDT'))
        # print(expected_sell_qty)

        # check last mkt order qty is proper
        self.assertTrue(strategy.exchange_interface.last_mkt_order['symbol'] == 'BTCUSDT')
        self.assertTrue(expected_sell_qty == float(strategy.exchange_interface.last_orders[2]['origQty']))

        # now check buy orders
        ltp = float(strategy.exchange_interface.last_mkt_order['fills'][0]['price'])
        expected_buy_price = ltp * (1 - (float(message.Configurations[0].Configuration.Levels[0].DownPercentage) / 100))
        self.assertTrue(expected_buy_price == float(strategy.exchange_interface.last_orders[0]['price']))

        expected_buy_price = ltp * (1 - (float(message.Configurations[0].Configuration.Levels[1].DownPercentage) / 100))
        self.assertTrue(expected_buy_price == float(strategy.exchange_interface.last_orders[1]['price']))

        # order_to_fill = copy.deepcopy(strategy.exchange_interface.last_orders[0])
        order_to_fill = {'status': 'FILLED',
                         'price': strategy.exchange_interface.last_orders[0]['price'],
                         'executedQty': strategy.exchange_interface.last_orders[0]['origQty']}

        strategy.exchange_interface.filled_orders[int(strategy.exchange_interface.last_orders[0]['orderId'])] = \
            order_to_fill

        strategy.poll_for_fills()
        print(f"Lastorders2: {strategy.exchange_interface.last_orders}")

        order_to_fill = {'status': 'FILLED',
                         'price': strategy.exchange_interface.last_orders[1]['price'],
                         'executedQty': strategy.exchange_interface.last_orders[1]['origQty']}

        strategy.exchange_interface.filled_orders[int(strategy.exchange_interface.last_orders[1]['orderId'])] = \
            order_to_fill

        strategy.poll_for_fills()

        order_to_fill = {'status': 'FILLED',
                         'price': strategy.exchange_interface.last_orders[3]['price'],
                         'executedQty': strategy.exchange_interface.last_orders[3]['origQty']}

        strategy.exchange_interface.filled_orders[int(strategy.exchange_interface.last_orders[3]['orderId'])] = \
            order_to_fill

        strategy.poll_for_fills()

        order_to_fill = {'status': 'FILLED',
                         'price': strategy.exchange_interface.last_orders[4]['price'],
                         'executedQty': strategy.exchange_interface.last_orders[4]['origQty']}

        strategy.exchange_interface.filled_orders[int(strategy.exchange_interface.last_orders[4]['orderId'])] = \
            order_to_fill

        strategy.exchange_interface.cancel_all_called = False
        strategy.exchange_interface.cancel_all_called_symbol = ""

        strategy.poll_for_fills()

        self.assertTrue(strategy.exchange_interface.cancel_all_called)
        self.assertTrue(strategy.exchange_interface.cancel_all_called_symbol == "BTCUSDT")

    def test_level_zero_sell_execution(self):
        txt = Path("StrategyConfigurationNew_one.json").read_text()
        message = json.loads(txt, object_hook=lambda d: SimpleNamespace(**d))
        queue = multiprocessing.Queue()
        parent_queue = multiprocessing.Queue()
        strategy = StrategyClassPoll(message, queue, parent_queue, "", DummyExchangeInterface, DummpMessagingProducer,
                                     DummyRedisInterface)
        ret = strategy.initialize_bot()
        self.assertTrue(ret)

        # print(strategy.exchange_interface.last_mkt_order)
        self.assertTrue(strategy.exchange_interface.last_mkt_order['symbol'] == 'BTCUSDT')
        # print(f" Price: {strategy.get_price_for_crypto_in_usd('BTCUSDT')}")
        # print(f"Lastorders1: {strategy.exchange_interface.last_orders}")
        self.assertTrue(len(strategy.exchange_interface.last_orders) == 3)

        level_zero_budget = float(message.Configurations[0].Configuration.LevelZeroUSDBudget)
        budget_multiplier = float(message.Configurations[0].Configuration.BudgetMultiplier)
        symbol_price = strategy.get_price_for_crypto_in_usd('BTCUSDT')

        expected_sell_qty = (level_zero_budget * budget_multiplier) / symbol_price
        expected_sell_qty = round(expected_sell_qty, strategy.exchange_interface.get_qty_precision('BTCUSDT'))
        # print(expected_sell_qty)

        # check last mkt order qty is proper
        self.assertTrue(strategy.exchange_interface.last_mkt_order['symbol'] == 'BTCUSDT')
        self.assertTrue(expected_sell_qty == float(strategy.exchange_interface.last_orders[2]['origQty']))

        # now check buy orders
        ltp = float(strategy.exchange_interface.last_mkt_order['fills'][0]['price'])
        expected_buy_price = ltp * (1 - (float(message.Configurations[0].Configuration.Levels[0].DownPercentage) / 100))
        self.assertTrue(expected_buy_price == float(strategy.exchange_interface.last_orders[0]['price']))

        expected_buy_price = ltp * (1 - (float(message.Configurations[0].Configuration.Levels[1].DownPercentage) / 100))
        self.assertTrue(expected_buy_price == float(strategy.exchange_interface.last_orders[1]['price']))

        # order_to_fill = copy.deepcopy(strategy.exchange_interface.last_orders[0])
        order_to_fill = {'status': 'FILLED',
                         'price': strategy.exchange_interface.last_orders[2]['price'],
                         'executedQty': strategy.exchange_interface.last_orders[2]['origQty']}

        strategy.exchange_interface.filled_orders[int(strategy.exchange_interface.last_orders[2]['orderId'])] = \
            order_to_fill

        strategy.exchange_interface.cancel_all_called = False
        strategy.exchange_interface.cancel_all_called_symbol = ""

        strategy.poll_for_fills()

        self.assertTrue(strategy.exchange_interface.cancel_all_called)
        self.assertTrue(strategy.exchange_interface.cancel_all_called_symbol == "BTCUSDT")

        print(f"Lastorders2: {strategy.exchange_interface.last_orders}")


if __name__ == '__main__':
    unittest.main()
