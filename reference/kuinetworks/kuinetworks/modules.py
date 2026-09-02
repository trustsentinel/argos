from .peers import Peer
from typing import AsyncGenerator

class BaseNetworkModule:
    async def get_peers(self, maxpeers_per_seed: int) -> AsyncGenerator[Peer, None]:
        raise NotImplementedError
