"""
Helper methods for creating the kafka-python KafkaProducer and KafkaConsumer objects.
"""
import time

import os
import json
import ssl
from tempfile import NamedTemporaryFile
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

from base64 import standard_b64encode

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

from kafka import KafkaProducer, KafkaConsumer
from confluent_kafka import Producer, Consumer, KafkaError

def get_kafka_brokers():
    """
    Parses the KAKFA_URL and returns a list of hostname:port pairs in the format
    that kafka-python expects.
    """
    # NOTE: The Kafka environment variables need to be present. If using
    # Apache Kafka on Heroku, they will be available in your app configuration.
    if not os.environ.get('KAFKA_URL'):
        raise RuntimeError('The KAFKA_URL config variable is not set.')

    return ['{}:{}'.format(parsedUrl.hostname, parsedUrl.port) for parsedUrl in
            [urlparse(url) for url in os.environ.get('KAFKA_URL').split(',')]]


def get_kafka_ssl_context():
    """
    Returns an SSL context based on the certificate information in the Kafka config vars.
    """
    # NOTE: We assume that Kafka environment variables are present. If using
    # Apache Kafka on Heroku, they will be available in your app configuration.
    #
    # 1. Write the PEM certificates necessary for connecting to the Kafka brokers to physical
    # files.  The broker connection SSL certs are passed in environment/config variables and
    # the python and ssl libraries require them in physical files.  The public keys are written
    # to short lived NamedTemporaryFile files; the client key is encrypted before writing to
    # the short lived NamedTemporaryFile
    #
    # 2. Create and return an SSLContext for connecting to the Kafka brokers referencing the
    # PEM certificates written above
    #

    # stash the kafka certs in named temporary files for loading into SSLContext.  Initialize the
    # SSLContext inside the with so when it goes out of scope the files are removed which has them
    # existing for the shortest amount of time.  As extra caution password
    # protect/encrypt the client key
    with NamedTemporaryFile(suffix='.crt') as cert_file, \
         NamedTemporaryFile(suffix='.key') as key_file, \
         NamedTemporaryFile(suffix='.crt') as trust_file:
        cert_file.write(os.environ['KAFKA_CLIENT_CERT'].encode('utf-8'))
        cert_file.flush()

        # setup cryptography to password encrypt/protect the client key so it's not in the clear on
        # the filesystem.  Use the generated password in the call to load_cert_chain
        passwd = standard_b64encode(os.urandom(33))
        private_key = serialization.load_pem_private_key(
            os.environ['KAFKA_CLIENT_CERT_KEY'].encode('utf-8'),
            password=None,
            backend=default_backend()
        )
        pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.BestAvailableEncryption(passwd)
        )
        key_file.write(pem)
        key_file.flush()

        trust_file.write(os.environ['KAFKA_TRUSTED_CERT'].encode('utf-8'))
        trust_file.flush()

        # create an SSLContext for passing into the kafka provider using the create_default_context
        # function which creates an SSLContext with protocol set to PROTOCOL_SSLv23, OP_NO_SSLv2,
        # and OP_NO_SSLv3 when purpose=SERVER_AUTH.
        ssl_context = ssl.create_default_context(
            purpose=ssl.Purpose.SERVER_AUTH, cafile=trust_file.name)
        ssl_context.load_cert_chain(cert_file.name, keyfile=key_file.name, password=passwd)

        # Intentionally disabling hostname checking.  The Kafka cluster runs in the cloud and Apache
        # Kafka on Heroku doesn't currently provide stable hostnames.  We're pinned to a specific certificate
        # for this connection even though the certificate doesn't include host information.  We rely
        # on the ca trust_cert for this purpose.
        ssl_context.check_hostname = False


        bot_settings = {}
        bot_settings['bootstrap.servers'] = 'ec2-100-25-107-37.compute-1.amazonaws.com:9096'
        bot_settings['group.id'] = 'mygroup'
        bot_settings['client.id'] = 'client-1'
        bot_settings['enable.auto.commit'] = True
        bot_settings['session.timeout.ms'] = 6000
        bot_settings['security.protocol'] = 'SSL'
        bot_settings['default.topic.config'] = {'auto.offset.reset':'smallest'}
        bot_settings['ssl.ca.location'] = cert_file.name
        bot_settings['ssl.key.location'] = key_file.name
        bot_settings['ssl.certificate.location'] = cert_file.name
        bot_settings['ssl.key.password'] = passwd

        kafka_bot_consumer = Consumer(bot_settings)
        kafka_bot_consumer.subscribe(["Market-Data"])                
        time.sleep(10)


    return ssl_context




