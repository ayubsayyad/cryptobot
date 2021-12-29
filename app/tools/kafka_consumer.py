from kafka import KafkaConsumer
import  messaging.kafka_messaging


consumer = messaging.kafka_messaging.get_consumer('', 'cumberland-30347.Bot_Updates')
print('consumer created')

for message in consumer:
    # message value and key are raw bytes -- decode if necessary!
    # e.g., for unicode: `message.value.decode('utf-8')`
    print ("%s:%d:%d: key=%s value=%s" % (message.topic, message.partition,
                                          message.offset, message.key,
                                          message.value))
