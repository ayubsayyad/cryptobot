from kafka import KafkaConsumer
import  messaging.kafka_messaging


#consumer = messaging.kafka_messaging.get_consumer('', 'cumberland-30347.Bot_Updates')
consumer = messaging.kafka_messaging.get_consumer('', 'cumberland-30347.Configuration_Update')
print('consumer created')

while True:
    msgs = consumer.poll(5)
    for tp, message in msgs.items():
        print(tp)
        for msg in message:
            print(f"message:  {msgs}")
            print(f"message:  {type({message})}")
            print(msg.value)

for message in consumer:
    # message value and key are raw bytes -- decode if necessary!
    # e.g., for unicode: `message.value.decode('utf-8')`
    print(f"message:  {message}")
#    print ("%s:%d:%d: key=%s value=%s" % (message.topic, message.partition,
#                                          message.offset, message.key,
#                                          message.value))
