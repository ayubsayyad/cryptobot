#from  binance import Client, AsyncClient
#from binance.streams import BinanceSocketManager

#import asyncio
#import config as c #from config.py
#import infinity as inf #userdefined function for infinity (probably not needed)
#from binance import AsyncClient, DepthCacheManager, Client
from binance import Client, ThreadedWebsocketManager, ThreadedDepthCacheManager
from binance.enums import *
from binance.exceptions import BinanceAPIException



#"aP0q0oEd7q5BPXVOWAans2yssuM2ZtlSDVv8QPOSUqYkxSeACZhnlgdGgsNkRbhC", "MHdyNt5uKjfq42oGpo0cUHUDKoZ1evfnZTt4KqwZ004FQnRUBwT9nGV7TrGpXfse", testnet=True
import asyncio
from binance import AsyncClient, BinanceSocketManager


async def main():
    client = await AsyncClient.create("aP0q0oEd7q5BPXVOWAans2yssuM2ZtlSDVv8QPOSUqYkxSeACZhnlgdGgsNkRbhC", "MHdyNt5uKjfq42oGpo0cUHUDKoZ1evfnZTt4KqwZ004FQnRUBwT9nGV7TrGpXfse", testnet=True)
#    res = await client.get_all_orders(symbol = "USDTBTC")
    res = await client.get_all_orders(symbol='BNBBTC', requests_params={'timeout': 5})
    print(res)
#    res = await client.get_exchange_info()


#    res = await client.cancel_order(symbol = 'BNBBTC', orderId = 3986)
#    print(res)
    

    order = async client.create_order(symbol='BNBBTC', side=SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=0.1)
#    order = await client.create_order(symbol='BNBBTC', side=SIDE_SELL, type=ORDER_TYPE_LIMIT, timeInForce=TIME_IN_FORCE_GTC, quantity=0.1, price=str(0.01))
    print(order)

    bm = BinanceSocketManager(client)
    # start any sockets here, i.e a trade socket
#    ts = bm.trade_socket('BNBBTC')
    ts = bm.user_socket()

    # then start receiving messages
    async with ts as tscm:
        while True:
            print('waiting')
            res = await tscm.recv()
            print(res)

    await client.close_connection()

if __name__ == "__main__":

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
