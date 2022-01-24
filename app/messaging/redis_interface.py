import redis
import os


class RedisInterface:
    def __init__(self):
        self.redis_conn = redis.from_url(os.getenv('REDIS_URL'))
        pass

    def get(self, symbol):
        if self.redis_conn:
            price = self.redis_conn.get(symbol)
            if price:
                print(f'price from redis: {price}')
                return float(price)

        return None
