
class MarketDataMessage:
    def __init__(self):
        self.symbol = ""
        self.price = 0

    def set_data(self, symbol, price):
        self.symbol = symbol
        self.price = price

    def set_data_from_json(self, jsonmessage):
        self.symbol = jsonmessage['Symbol']
        self.price = jsommessage['Price']

