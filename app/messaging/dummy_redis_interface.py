
class DummyRedisInterface:
    def __init__(self):
        pass

    def get(self, symbol):
        if symbol == "BTCUSDT":
            return 43005.91
        elif symbol == "BNBUSDT":
            return 493.0
        elif symbol == "MATICUSDT":
            return 2.290
        return None
