import logging

import pika
import json


log: logging.Logger = logging.getLogger("publisher")

class PeerEventPublisher:
    def __init__(self, host, exchange, username, password):
        credentials = pika.PlainCredentials(username, password)
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=host, credentials=credentials))
        self.channel = self.connection.channel()
        self.exchange = exchange
        self.channel.exchange_declare(exchange=self.exchange, exchange_type='fanout')

    def publish_event(self, network, address, port, public_key, source):
        event_data = {
            'network': network,
            'address': address,
            'port': port,
            'public_key': public_key,
            'source': source
        }

        self.channel.basic_publish(
            exchange=self.exchange,
            routing_key='', #f'network.{network}',
            body=json.dumps(event_data)
        )
        log.info(f" [x] Sent {event_data}")

    def close(self):
        log.info("Closing the connection")
        self.connection.close()
