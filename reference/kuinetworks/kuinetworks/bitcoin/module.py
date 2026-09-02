from ..modules import BaseNetworkModule
from ..peers import BTCPeer, Peer
from ..net import get_addresses
from .discovery import get_seeds
from typing import AsyncGenerator

class BTCModule(BaseNetworkModule):
    def __init__(self):
        self.id = "btc"
        self.seeds = get_seeds()
    
    async def get_peers(self, maxpeers_per_seed: int = 2) -> AsyncGenerator[Peer, None]:
        for seed_host, seed_port in self.seeds:
            depth=0
            for host, port in await get_addresses(seed_host, seed_port):
                if depth > maxpeers_per_seed:
                    break
                yield BTCPeer(host, port, (seed_host, seed_port))
                depth=depth+1
