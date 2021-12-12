from abc import ABC, abstractmethod

class IStrategyInterface(ABC):
    def __init__(self):
        super().__init__()


    @abstractmethod
    def on_market_data_update(self, marketDataMessage):
        pass

    @abstractmethod
    def on_configuration_update(self, configUpdateMessage):
        pass



