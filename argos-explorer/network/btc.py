import logging
import random

from bitcoin import btc
from core.addresses import get_addresses
from network.network import NetworkModule

log: logging.Logger = logging.getLogger("btc")

class BTCModule(NetworkModule):
    def __init__(self):
        self.id = "btc"
        self.seeds = btc.get_seeds()
        random.shuffle(self.seeds)

    async def get_peers(self, max_depth = 10):
        for seed_address, seed_port in self.seeds:
            depth = 0
            log.info(f'Touching the seed node={seed_address}:{seed_port}')
            for peer_address, peer_port in await get_addresses(seed_address, seed_port):
                depth +=1
                if depth > max_depth:
                    break
                log.info(f'\tnode={peer_address}:{peer_port}')
                # BTC doesn't use public keys in this context
                yield peer_address, peer_port, None, seed_address
