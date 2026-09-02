from bitcoin import btc
from ethereum import eth
from core.addresses import get_addresses

class NetworkModule:
    async def get_peers(self):
        raise NotImplementedError

