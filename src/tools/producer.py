from confluent_kafka import Producer
import socket
import sys
import json
from pathlib import Path
import redis


conf = {'bootstrap.servers': ":9092,:9092",
                'client.id': socket.gethostname()}

producer = Producer(conf)
print(str(producer))
topic  = sys.argv[1]
file_to_send  = sys.argv[2]

txt = Path(file_to_send).read_text()

producer.produce(topic, key="key", value=txt)
producer.poll(1)
print('sent')

