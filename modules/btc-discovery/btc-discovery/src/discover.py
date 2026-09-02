import logging

from src.bitcoin.connection import connect

# Example usage
configuration = {
    'port': 8333,
    'source_address': '0.0.0.0',
    'socket_timeout': 30,
    'protocol_version': 70016,
    'user_agent': '/minimal-client:0.1/',
    'onion': True,
    'i2p': True,
    'max_age': 300000,
    'i2p_proxies': [('127.0.0.1', 4444)],  # I2P proxy for .i2p addresses
    'tor_proxies': [('127.0.0.1', 9050)]   # Tor proxy for .onion addresses
}

address_list = [
   # ("7sn3u4fn46iozdkcv3cjicj3hw22qrzqnrz3nyogvgqgoghysffh2cqd.onion", 8333),
    ("64.225.71.231", 8333),
   # ("::ffff:40e1:47e7", 8333)
]

for address in address_list:
    result = connect(address, configuration)
    logging.info(result)
