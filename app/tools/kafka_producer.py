from kafka import KafkaConsumer
import  messaging.kafka_messaging
from os import path
import threading
import time
from pathlib import Path


kafka_producer = messaging.kafka_messaging.get_producer()
print('get_producer created')
txt = Path('app/messages/json/StrategyConfigurationNew.json').read_text()

future = kafka_producer.send('cumberland-30347.Configuration_Update', txt)
kafka_producer.flush()
print("sent")
time.sleep(10)