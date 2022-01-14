from kafka import KafkaConsumer
import  messaging.kafka_messaging
from os import path
import threading
import time
from pathlib import Path
import sys

kafka_producer = messaging.kafka_messaging.get_producer()
print('get_producer created')
path = sys.argv[1]
print(path)
txt = Path(path).read_text()

future = kafka_producer.send('cumberland-30347.Configuration_Update', txt)
kafka_producer.flush()

try:
    record_metadata = future.get(timeout=10)
except KafkaError:
    # Decide what to do if produce request failed...
    log.exception()
    pass

print("sent*****")
time.sleep(10)
