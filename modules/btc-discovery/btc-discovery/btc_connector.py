import random
import time
import struct
import logging
import hashlib
import socket
import traceback

import socks
from btc_protocol import deserialize_version_message
from btc_protocol_utils import serialize_version_msg

MAGIC_NUMBER = b'\xF9\xBE\xB4\xD9'
PROTOCOL_VERSION = 70016
USER_AGENT = '/minimal-client:0.1/'
HEIGHT = 754565
RELAY = 0

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class ConnectionError(Exception):
    pass

class ProtocolError(Exception):
    pass

def sha256(data):
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()


class Connection:
    def __init__(self, to_addr, from_addr, **conf):
        self.to_addr = to_addr
        self.from_addr = from_addr
        self.protocol_version = conf.get('protocol_version', PROTOCOL_VERSION)
        self.user_agent = conf.get('user_agent', USER_AGENT)
        self.height = conf.get('height', HEIGHT)
        self.relay = conf.get('relay', RELAY)
        self.socket_timeout = conf.get('socket_timeout', 30)
        self.proxy = conf.get('proxy')
        self.socket = None
        self.is_ipv6 = False
        self.network_type = "Unknown"
        self.protocol = "ipv4"

    def configure_proxy(self):
        """Set up the SOCKS proxy for .onion or .i2p addresses, or set default connection type."""
        if self.to_addr[0].endswith('.onion'):
            if not self.proxy:
                raise ConnectionError('Tor proxy is required for .onion addresses.')
            # Configure Tor SOCKS5 proxy
            socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, self.proxy[0], self.proxy[1])
            self.socket = socks.socksocket()
            self.protocol = "onion"
            self.network_type = "btc"
            logging.debug(f"Using Tor proxy for {self.to_addr[0]}:{self.to_addr[1]}")
        elif self.to_addr[0].endswith('.i2p'):
            if not self.proxy:
                raise ConnectionError('I2P proxy is required for .i2p addresses.')
            # Configure I2P SOCKS5 proxy
            socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, self.proxy[0], self.proxy[1])
            self.socket = socks.socksocket()
            self.protocol = "i2p"
            self.network_type = "btc"
            logging.debug(f"Using I2P proxy for {self.to_addr[0]}:{self.to_addr[1]}")
        else:
            # Detect if IPv6
            try:
                socket.inet_pton(socket.AF_INET6, self.to_addr[0])
                self.is_ipv6 = True
            except socket.error:
                pass

            # Configure IPv4/IPv6 connection
            if self.is_ipv6:
                self.socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
                self.protocol = "ipv6"
                logging.debug(f"Connecting to {self.to_addr[0]}:{self.to_addr[1]} via IPv6")
            else:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                logging.debug(f"Connecting to {self.to_addr[0]}:{self.to_addr[1]} via IPv4")

    def open(self):
        """Open the connection."""
        logging.debug(f"Attempting to open connection to {self.to_addr}")
        self.configure_proxy()  # Proxy setup logic here
        self.socket.settimeout(self.socket_timeout)
        self.socket.connect(self.to_addr)

    def close(self):
        """Close the socket connection."""
        if self.socket:
            self.socket.close()
            logging.info(f"Closed connection to {self.to_addr}")

    def handshake(self):
        """Perform the handshake and return the version message."""
        version_msg = serialize_version_msg(self.to_addr, self.from_addr, self.protocol_version, self.user_agent,
                                            self.height, self.relay)
        logging.debug(f"Sending handshake data: {version_msg.hex()}")
        self.send(version_msg)

        # Receive the response (version and verack)
        data = self.receive()
        logging.debug(f"Receiving data: {data.hex()}")

        # Deserialize the version message
        version_response = deserialize_version_message(data)
        logging.debug(f"Version message received:\n{version_response}")
        return version_response

    def send(self, msg):
        self.socket.sendall(msg)

    def receive(self):
        # Read the full header (24 bytes)
        header = self.socket.recv(24)
        if len(header) < 24:
            raise ValueError('Incomplete header received')

        # Extract payload length from the header (bytes 16 to 20)
        payload_length = struct.unpack('<I', header[16:20])[0]

        # Read the payload based on the length
        payload = self.socket.recv(payload_length)
        while len(payload) < payload_length:
            payload += self.socket.recv(payload_length - len(payload))

        return payload


def connect(address):
    proxy = None

    if address[0].endswith('.onion') and CONF['onion']:
        proxy = random.choice(CONF['tor_proxies'])
    elif address[0].endswith('.i2p') and CONF['i2p']:
        proxy = random.choice(CONF['i2p_proxies'])

    conn = Connection((address[0], int(address[1])),
                      (CONF['source_address'], 0),
                      socket_timeout=CONF['socket_timeout'],
                      proxy=proxy)
    try:
        conn.open()
        version_msg = conn.handshake()
        return f"Connected {address[0]}:{address[1]} network={conn.network_type}, protocol={conn.protocol}, version={version_msg}"
    except (ProtocolError, ConnectionError, socket.error) as err:
        traceback.print_exc()
        logging.error(f'{conn.to_addr}: {err}')
        return f"Not connected {address[0]}:{address[1]} network=Unknown, protocol={conn.protocol}, error={str(err)}"
    except Exception as err:
        traceback.print_exc()
        logging.error(f'{conn.to_addr}: {err}')
        return f"Not connected {address[0]}:{address[1]} network=Unknown, protocol={conn.protocol}, error={str(err)}"


# Example usage
CONF = {
    'port': 8333,
    'source_address': '0.0.0.0',
    'socket_timeout': 30,
    'protocol_version': 70016,
    'user_agent': '/minimal-client:0.1/',
    'onion': True,
    'i2p': True,
    'i2p_proxies': [('127.0.0.1', 4444)],  # I2P proxy for .i2p addresses
    'tor_proxies': [('127.0.0.1', 9050)]   # Tor proxy for .onion addresses
}

address_list = [
    ("7sn3u4fn46iozdkcv3cjicj3hw22qrzqnrz3nyogvgqgoghysffh2cqd.onion", 8333),
   # ("64.225.71.231", 8333),
   # ("::ffff:40e1:47e7", 8333)
]

for address in address_list:
    result = connect(address)
    logging.info(result)
