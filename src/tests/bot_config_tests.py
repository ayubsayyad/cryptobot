import unittest
import json
from messages.python.strategyconfigmessage import StrategyConfigMessage
from strategies.buydeepsellhighstrategy import BuyDeepSellHighStrategy
from messages.python.marketdatamessage import MarketDataMessage

class TestStringMethods(unittest.TestCase):
    def test_create_strategy_send_order(self):
        with open("tests/StrategyConfiguration.json") as outfile:
            data = outfile.read()
            jsondata = json.loads(data)
            message  = StrategyConfigMessage(jsondata)
            strategy = BuyDeepSellHighStrategy(message, True)
            exchnage_interface = strategy.get_exchange_interface()
            mktmsg = MarketDataMessage()
            mktmsg.set_data("USDTBTC", 49000)
            strategy.on_market_data_update(mktmsg)

            mktmsg.set_data("USDTBTC", 40000)
            strategy.on_market_data_update(mktmsg)
            mktmsg.set_data("USDTBTC", 60000)
            strategy.on_market_data_update(mktmsg)

    def test_read_config(self):
        print("running test_read_config ")
        with open("tests/StrategyConfiguration.json") as outfile:
            data = outfile.read()
#        print(data)
            jsondata = json.loads(data)
            message  = StrategyConfigMessage(jsondata)
            self.assertTrue(message is not None)

    def test_create_strategy(self):
        with open("tests/StrategyConfiguration.json") as outfile:
            data = outfile.read()
            jsondata = json.loads(data)
            message  = StrategyConfigMessage(jsondata)
            strategy = BuyDeepSellHighStrategy(message, True)


if __name__ == '__main__':
    unittest.main()





