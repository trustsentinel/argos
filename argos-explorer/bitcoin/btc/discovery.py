SEED_NODES = [
    ("seed.bitcoin.sipa.be", 8333),
    ("dnsseed.bluematt.me", 8333),
    ("dnsseed.bitcoin.dashjr.org", 8333),
    ("seed.bitcoinstats.com", 8333),
    ("seed.bitnodes.io", 8333),
    ("bitseed.xf2.org", 8333),
    ("seed.btc.petertodd.org", 8333),
    ("seed.bitcoin.jonasschnelli.ch", 8333)
]

def get_seeds():
    return SEED_NODES

# references: https://bitcoin.stackexchange.com/questions/38190/where-can-i-find-a-list-of-reliable-bitcoin-full-nodes
# more nodes: https://github.com/bitcoin/bitcoin/blob/master/contrib/seeds/nodes_main.txt