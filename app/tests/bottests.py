import unittest
from strategies.strategyfactory import StrategyFactory
from strategies.buydeepsellhighstrategy import BuyDeepSellHighStrategy

class TestStringMethods(unittest.TestCase):
    def test_strategy_creation_not_available(self):
        factory = StrategyFactory()
        strategy_inst = factory.create_strategy("")
        self.assertTrue(strategy_inst is None)

    def test_strategy_creation_available(self):
        factory = StrategyFactory()
        strategy_inst = factory.create_strategy("BuyDeepSellHigh")
        self.assertTrue(strategy_inst is not None)        

if __name__ == '__main__':
    unittest.main()



