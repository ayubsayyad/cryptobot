import os
import time
import kafka_helper


producer = kafka_helper.get_kafka_producer()
future = producer.send('cumberland-30347.Market-Data', 'my key')
# Block for 'synchronous' sends
try:
    record_metadata = future.get(timeout=10)
except KafkaError:
    # Decide what to do if produce request failed...
    log.exception()
    pass

print("produced", flush=True)

consumer = kafka_helper.get_kafka_consumer(topic='cumberland-30347.Market-Data')
for message in consumer:
    print("message:", flush=True)
    print(message, flush=True)

time.sleep(10)
