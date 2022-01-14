import  messaging.kafka_messaging


class KafkaMessagingProducer:
    def __init__(self) -> None:
        self.kafka_producer = messaging.kafka_messaging.get_producer()
    

    def send(self, topic, message_string):
        self.kafka_producer.send(topic, message_string)
        self.kafka_producer.flush()
        print(f"sent on kafka: {topic}: {message_string}")


class KafkaMessagingConsumer:
    def __init__(self, topic_list) -> None:
        self.kafka_consumer = messaging.kafka_messaging.get_consumer('', topic_list)
    

    def poll(self, timeout=2):
        kafka_msg = self.kafka_consumer.poll(timeout)
        return kafka_msg



class DummpMessagingProducer:
    def __init__(self) -> None:
        self.published_message = []
    

    def send(self, topic, message_string):
        self.published_message.append(message_string)
        print(f"sent on dummy: {topic}: {message_string}")


class Val:
    def __init__(self, message) -> None:
        self.value= message

class DummyMessagingConsumer:
    def __init__(self, topic_list) -> None:
        self.message_to_send = None
        self.topic_list = topic_list
    


            
    def poll(self, timeout=2):
        if self.message_to_send:
            messages = {}
            msg_list = []
            
            msg_list.append(Val(self.message_to_send))
            messages[self.topic_list] = msg_list
            self.message_to_send = None
            return messages
        else:
            return {}

