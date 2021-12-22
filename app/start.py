import os
import time
import kafka_helper

pro = kafka_helper.get_kafka_producer()
pro.send('Market-Data', key='my key', value={'k': 'v'})


consumer = kafka_helper.get_kafka_consumer(topic='Market-Data')
for message in consumer:
    print(message)

time.sleep(10)
