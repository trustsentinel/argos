import logging
import asyncio

from amqp.consumer import PeerEventConsumer
from core.config import ConfigLoader
from btc import btc
from core.es import ElasticsearchClient

log: logging.Logger = logging.getLogger("btc_processer")
processor: PeerEventConsumer = None

def only_btc_events(event_data):
    return event_data['network'] == 'btc'

async def btc_processing(es: ElasticsearchClient):
    async def process_event_by_elasticsearch_client(evt):
        return await btc.process(es, evt)
    return process_event_by_elasticsearch_client

async def process():
    global processor
    config = ConfigLoader()
    es = ElasticsearchClient(
        host = config.get("elasticsearch.host", "localhost"),
        port = config.get("elasticsearch.port", 9200),
        index = config.get("elasticsearch.index", "peers")
    )
    event_processor = await btc_processing(es)
    processor = PeerEventConsumer(
        host=config.get("amqp.host"),
        exchange=config.get("amqp.exchange"),
        queue=config.get("amqp.queue"),
        username=config.get("amqp.username"),
        password=config.get("amqp.password"),
        event_processor=event_processor,
        filter_logic=only_btc_events
    )
    await processor.consume()
    try:
        await asyncio.Event().wait()  # Wait forever until interrupted
    except asyncio.CancelledError:
        pass

async def close():
    global processor
    if processor:
        await processor.close()