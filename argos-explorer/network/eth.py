from ethereum import eth
from network.network import NetworkModule

class ETHModule(NetworkModule):
    def __init__(self):
        self.id = "eth"
        self.bootnodes = eth.get_bootnodes()

    async def get_peers(self):
        source = self.bootnodes[0] # select the first node
        for peer_address, peer_port, peer_public_key in await eth.get_neighbours(source):
            print(peer_address, peer_port, peer_public_key)
            yield peer_address, peer_port, peer_public_key, source

