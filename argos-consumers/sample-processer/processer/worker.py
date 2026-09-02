import logging

from amqp.consumer import PeerEventConsumer
from core.config import ConfigLoader
from processer import sample

log: logging.Logger = logging.getLogger("peer_processer")
processor: PeerEventConsumer = None

def filter_by_network(network_type):
    def filter_event_data_by_network(event_data):
        return event_data['network'] == network_type
    return filter_event_data_by_network

async def process(network_type):
    global processor
    config = ConfigLoader()
    processor = PeerEventConsumer(
        host=config.get("amqp.host"),
        exchange_name=config.get("amqp.exchange"),
        queue_name=config.get("amqp.queue"),
        username=config.get("amqp.username"),
        password=config.get("amqp.password"),
        event_processor=sample.process,
        filter_logic=filter_by_network(network_type)
    )
    processor.consume()


async def close():
    global processor
    if processor:
        processor.close()