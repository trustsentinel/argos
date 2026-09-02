import logging
import asyncio

from core.config import ConfigLoader
from core.publisher import PeerEventPublisher
from network.btc import BTCModule
from network.eth import ETHModule

log: logging.Logger = logging.getLogger("worker")

network_selector = { "btc" : BTCModule, "eth" : ETHModule }

peer_publisher: PeerEventPublisher = None

async def process(network_type : str, max_peers: int, max_depth: int):
    global peer_publisher
    config = ConfigLoader()
    peer_publisher = PeerEventPublisher(
        host=config.get("rabbitmq.host"),
        exchange=config.get("rabbitmq.exchange"),
        username=config.get("rabbitmq.username"),
        password=config.get("rabbitmq.password")
    )
    network = network_selector[network_type]()
    total_peers = 0
    async for address, port, public_key, seed in network.get_peers(max_depth):
        total_peers += 1
        if total_peers > max_peers:
            break

        await asyncio.sleep(1)

        log.info(f"retrieved {network.id} node address={address}, port={port}, public_key={public_key}, seed={seed}")
        peer_publisher.publish_event(
            network=network.id,
            address=address,
            port=port,
            public_key=public_key,
            source=seed
        )

async def close():
    global peer_publisher
    peer_publisher.close()