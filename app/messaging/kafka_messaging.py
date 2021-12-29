import os
import time
import kafka_helper
from confluent_kafka import Producer, Consumer, KafkaError
import socket
import sys
import json
from pathlib import Path
import copy

def get_producer(is_heroku=True):
    if is_heroku:
        producer = kafka_helper.get_kafka_producer()
        return producer
    else:
        conf = {'bootstrap.servers': ":9092,:9092",
                'client.id': socket.gethostname()}
        producer = Producer(conf)
        return producer



def get_consumer(group_id, topics, is_heroku=True):
    if is_heroku:
        if not os.environ.get('KAFKA_PREFIX'):
            raise RuntimeError('The KAFKA_PREFIX config variable is not set.')
        topic_list = copy.deepcopy(topics) 
        topic_prefix = os.environ.get('KAFKA_PREFIX')
        [f'{topic_prefix}{topic}' for topic in topic_list]
        consumer = kafka_helper.get_kafka_consumer(topic=topic_list, group_id = group_id)
        print(topic_list)
        return consumer
    else:
        kafka_settings = config['kafka']
        bot_settings = copy.deepcopy(kafka_settings)

        bot_settings['group.id'] = group_id
        
        kafka_consumer = Consumer(bot_settings)
        kafka_consumer.subscribe(topics)
        return kafka_consumer

