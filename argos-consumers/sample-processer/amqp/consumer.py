import pika
import json
import logging

log: logging.Logger = logging.getLogger("consumer")

class PeerEventConsumer:
    def __init__(self, host, exchange_name, queue_name, username, password, filter_logic=None, event_processor=None):
        credentials = pika.PlainCredentials(username, password)
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=host, credentials=credentials))
        self.channel = self.connection.channel()

        self.exchange_name = exchange_name
        self.queue_name = queue_name
        self.event_processor = event_processor
        self.filter_logic = filter_logic

        self.channel.exchange_declare(exchange=self.exchange_name, exchange_type='fanout')
        self.channel.queue_declare(queue=self.queue_name)
        self.channel.queue_bind(exchange=self.exchange_name, queue=self.queue_name)

    def callback(self, ch, method, properties, body):
        event_data = json.loads(body)

        if self.filter_logic:
            if not self.filter_logic(event_data):
                log.info(f" [x] Skipping event: {event_data}")
                return

        log.info(f" [x] Processing event: {event_data}")
        self.event_processor(event_data)

    def consume(self):
        self.channel.basic_consume(queue=self.queue_name, on_message_callback=self.callback, auto_ack=True)
        log.info(f" [*] Waiting for messages in {self.queue_name}. To exit press CTRL+C")
        self.channel.start_consuming()

    def close(self):
        log.info("Closing the connection")
        self.connection.close()
