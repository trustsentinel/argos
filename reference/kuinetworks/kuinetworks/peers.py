class Peer():
    def __init__(self, host, port, network_type, public_key = None, seed = None):
        self.id = f"{host}:{port}"
        self.network_type = network_type
        self.host = host
        self.port = port
        self.public_key = public_key
        self.seed = seed
        
class BTCPeer(Peer):
    def __init__(self, host, port, seed = None):
        super().__init__(host, port, "btc", None, seed)