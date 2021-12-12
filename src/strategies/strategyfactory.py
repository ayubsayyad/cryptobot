from strategies.istrategyinterface import IStrategyInterface
from strategies.buydeepsellhighstrategy import BuyDeepSellHighStrategy

class StrategyFactory:
    def create_strategy(self, strategy_name):
        if strategy_name == "BuyDeepSellHigh":
            return BuyDeepSellHighStrategy
        elif strategy_name == "BuyDeepSellHigh2":
            return BuyDeepSellHighStrategy
        else:
            pass
