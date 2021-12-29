import asyncio
import copy
import json
import multiprocessing
from os import path
import threading
import time
from pathlib import Path

from multiprocessing import Process
from types import SimpleNamespace
from binance import Client, AsyncClient, ThreadedWebsocketManager, ThreadedDepthCacheManager, BinanceSocketManager
from binance.enums import *
from binance.exceptions import BinanceAPIException
from exchanges.binance_async_interface import Binance_Async_Interface
import  messaging.kafka_messaging

class Levels:
    def __init__(self, level, qty_unit, initial_price):
        self.qty_to_trade = float(level.Qty) * qty_unit
        self.percentage = float(level.Percentage)
        self.price_to_send = initial_price * (1 - (self.percentage/100))
        self.buy_executed = False
        self.sell_executed = False
        self.buy_order = None
        self.sell_order = None
        
    
class CryptoLevel:
    def __init__(self, conf):
        self.crypto = conf.Configuration.Crypto
        initial_price = float(conf.Configuration.InitialPrice)
        qty_unit = float(conf.Configuration.QtyUnit)
        self.sell_percent = float(conf.Configuration.SellPercent)
        self.levels = []
        for level in conf.Configuration.levels:
            lvl = Levels(level, qty_unit, initial_price)
            self.levels.append(lvl)

class StrategyClass:
    def __init__(self, message, queue, parent_queue):
        self.message = message
        self.p = messaging.kafka_messaging.get_producer()
        self.iface = Binance_Async_Interface(message, queue)
        self.kafka_producer = messaging.kafka_messaging.get_producer()
        self.queue = queue
        self.parent_queue = parent_queue
        self.cryptlevels = {}
        for conf in self.message.Configurations:
            crypto = conf.Configuration.Crypto
            cryptolvl = CryptoLevel(conf)
            self.cryptlevels[crypto] = cryptolvl

    async def create_connection(self):
        await self.iface.create()

    async def cancel_all(self):
        await self.iface.cancel_all()

    def wait_on_clients(self):
        self.iface.bridge_func()


    async def send_orders_for_crypto(self):
        for crypto, conf in self.cryptlevels.items():
            ret = await self.send_orders(crypto, conf)
            if ret == False:
                await self.cancel_all()
                return False

    async def send_orders(self, crypto, conf):
        for level in conf.levels:
            order = await self.send_order(crypto, SIDE_BUY, level.qty_to_trade, level.price_to_send)
            if order is not None:
                level.buy_order  = order
                print(order)
            else:
                print("Error sending order")
                return False
        return True

    async def send_order(self, symbol, side , qty, price):
        order = await self.iface.send_order(symbol, side, ORDER_TYPE_LIMIT, TIME_IN_FORCE_GTC, qty, price)
        #copied_order = copy.deepcopy(order)
        #copied_order[""]
        return order

    async def send_sell_order(self, cryptlevel, level, symbol, executedQty, price):
        qty = max(level.qty_to_trade, executedQty)
        sell_price = price * (1 + (cryptlevel.sell_percent/100))
        order = await self.send_order(symbol, SIDE_SELL, qty, sell_price)
        level.sell_order = order
        print(f"sell order sent at price: {sell_price}")

    def send_message_to_kafka(self, json_string):
        future = self.kafka_producer.send('cumberland-30347.Bot_Updates', json_string)
        self.kafka_producer.flush()
        print("sent on kafka: cumberland-30347.Bot_Updates")        

    def on_account_info(self, message):
        print(message)
        json_string = json.dumps(message, indent = 2)
        self.send_message_to_kafka(json_string)
    
    def on_error(self, message):
        json_string = json.dumps(message, indent = 2)
        self.send_message_to_kafka(json_string)
        pass


    def on_new_order(self, message):
        pass

    def on_order_update(self, message):
        pass    

    def on_execution_report(self, message):
        print("on_execution_report")
        symbol = message["s"]
        order_id = int(message["i"])
        #order = self.iface.get_order(symbol, order_id)
        #print(f'**************************** {order}')

    def get_level(self, symbol, orderId, side):
        ret = self.cryptlevels.get(symbol)
        if None == ret:
            return (None, None)
        for level in ret.levels:
            if side == 'BUY' and level.buy_order != None and orderId == int(level.buy_order['orderId']):
                return (ret, level)
            else:
                if (level.sell_order != None and orderId == int(level.sell_order['orderId'])):
                    return (ret, level)
        return (None, None)



    async def if_all_orders_complete_refersh(self, symbol, cryptlevel, conf):
        for level in conf.levels:
            if level.sell_executed and level.buy_executed:
                pass
            else:
                return False
        
        print("*************************** if_all_orders_complete_refersh ******************************")
        for level in conf.levels:
            level.sell_executed = False
            level.buy_executed = False
            level.sell_order = None
            level.buy_order = None

        await self.send_orders(symbol, cryptlevel)


    async def on_fill(self, message):
        price = float(message['price'])
        executedQty = float(message['executedQty'])
        symbol = message['symbol']
        side = message['side']
        orderId = int(message['orderId'])
        cryptlevel, level = self.get_level(symbol, orderId, side)
        if None == level:
            print("Error could not get order")
        
        if  side == 'BUY':
            level.buy_executed = True
            await self.send_sell_order(cryptlevel, level, symbol, executedQty, price)
        else:
            level.sell_executed = True


    async def on_order_status(self, message):
        print("on_execution_report")
        if message["status"] == "FILLED":
            await self.on_fill(message)

        json_string = json.dumps(message, indent = 2)
        self.send_message_to_kafka(json_string)

    def on_exchange_response(self, message):
        print(message)
        json_string = json.dumps(message, indent = 2)
        self.send_message_to_kafka(json_string)
        
    async def on_add_new_crypto(self, message):

        pass


    async def process_message(self, message):
        if "Type" not in message:
            print(f"Invalid message: {message}")
            return

        if message["Type"] == "ExchangeResponseAccount":
            self.on_exchange_response(message)

        elif message["Type"] == "BalanceExchangeResponse":
            self.on_exchange_response(message)

        elif message["Type"] == "ExecutionReport":
            print("************************************")
            self.on_execution_report(message)

        elif message["Type"] == "BinanceErrorOccured":
            self.on_exchange_response(message)
            pass
        elif message["Type"] == "OrderStatus":
            await self.on_order_status(message)
        elif message["Type"] == "AddNewCrypto":
            await self.on_add_new_crypto(message)            
        else:
            print("Message type not handled")
        

    async def bot_runner(self):
        await self.create_connection()
        if not self.iface.initialized:
            print("Error running binance interface")
            return None
    
        await self.cancel_all()

        x = threading.Thread(target=self.wait_on_clients)
        x.start()
        time.sleep(1)
        ret = await self.send_orders_for_crypto()
        if False == ret:
            print("Bot failed to send initial orders, please check reason and restart")
            message = {}

            
            message["Type"] = "TerminateMe"
            message["Client"] = self.message.clinet_details.Client_Id
            self.parent_queue.put(message)

            return

        print("Waiting on queue!")
        while True:
            if not self.queue.empty():
                msg = self.queue.get()
                if isinstance(msg, dict):
                    await self.process_message(msg)
                else:
                    print("Not dictionary  ***********")
            else:
                time.sleep(5)
                

def main(config, queue, parent_queue):
    #f = open(config,)
    x = json.loads(config, object_hook=lambda d: SimpleNamespace(**d))
    strategy = StrategyClass(x, queue, parent_queue)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(strategy.bot_runner())
    loop.close()

def send_message_to_kafka(kafka_producer, json_string):
    future = kafka_producer.send('cumberland-30347.Bot_Updates', json_string)
    kafka_producer.flush()
    print("sent on kafka: cumberland-30347.Bot_Updates")


def start_new_bot(running_bots, txt, parent_queue):
    try:
        msg = json.loads(txt, object_hook=lambda d: SimpleNamespace(**d))
        if msg.clinet_details.Client_Id in running_bots:
            print("Bot already running")
            return False

        queue = multiprocessing.Queue()
        proc = Process(target = main, args=(txt, queue, parent_queue))
        
        proc.start()
        running_bots[msg.clinet_details.Client_Id] = (proc, queue)
        return True
    except Exception as e:
        print("exception creating bot")
        return False

    pass

if __name__ == "__main__":

    parent_queue = multiprocessing.Queue()
    running_bots = {} 
#    txt = Path('app/messages/json/StrategyConfigurationNew.json').read_text()
    #start_new_bot(running_bots, txt, parent_queue)

    kafka_producer = messaging.kafka_messaging.get_producer()
    consumer = messaging.kafka_messaging.get_consumer('', 'cumberland-30347.Configuration_Update')

    while True:
        if not parent_queue.empty():
            msg = parent_queue.get()
            if isinstance(msg, dict):
                if msg["Type"] == "TerminateMe":
                    if msg["Client"] in running_bots:
                        proc, q = running_bots[msg["Client"]]
                        print("terminating process")
                        proc.terminate()
                        msg["Type"] = "ProcessTerminated"
                        json_string = json.dumps(msg, indent = 2)
                        send_message_to_kafka(kafka_producer, json_string)
            else:
                print("Not dictionary  ***********")
        
        else:
            kafka_msg = consumer.poll(5)
            if  0 != len(kafka_msg):
                for topic, kafka_messages in kafka_msg.items():
                    for msg in kafka_messages:
                        jsondata = json.loads(msg.value)
                        if jsondata["Type"] == "StrategyConfigurationNew":
                            if start_new_bot(running_bots, msg.value, parent_queue):
                                print("New bot started")
            else:
                print("Running.")
                for key, val in list(running_bots.items()):
                    print(val)
                    if not val[0].is_alive():
                        res = running_bots.pop(key, None)
                        if None != res:
                            print(f"bot terminited, removed key: {key}")

                time.sleep(5)



