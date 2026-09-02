import aio_pika
import json
import logging
import asyncio

log: logging.Logger = logging.getLogger("consumer")


class PeerEventConsumer:
    def __init__(self, host, exchange, queue, username, password, filter_logic=None, event_processor=None):
        self.channel = None
        self.host = host
        self.exchange = exchange
        self.queue = queue
        self.username = username
        self.password = password
        self.filter_logic = filter_logic
        self.event_processor = event_processor

    async def connect(self):
        connection = await aio_pika.connect_robust(
            f"amqp://{self.username}:{self.password}@{self.host}/"
        )
        self.channel = await connection.channel()

        await self.channel.declare_exchange(self.exchange, aio_pika.ExchangeType.FANOUT)
        self.queue = await self.channel.declare_queue(self.queue)
        await self.queue.bind(self.exchange)

        log.info(f"Connected to RabbitMQ at {self.host} and bound to queue {self.queue}")

    async def process_message(self, message: aio_pika.IncomingMessage):
        async with message.process():
            event_data = json.loads(message.body)

            if self.filter_logic and not self.filter_logic(event_data):
                log.info(f" [x] Skipping event: {event_data}")
                return

            log.info(f" [x] Processing event: {event_data}")
            await self.event_processor(event_data)

    async def consume(self):
        await self.connect()
        await self.queue.consume(self.process_message)

    async def close(self):
        await self.channel.close()
        log.info("Closing the connection")
