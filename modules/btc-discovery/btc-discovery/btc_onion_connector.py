import random
import time
import struct
import logging
import hashlib
import socket
import socks
from io import BytesIO
import struct
import time
import random
import hashlib
import socket

from btc_protocol import deserialize_version_message
from btc_protocol_utils import serialize_version_msg

MAGIC_NUMBER = b'\xF9\xBE\xB4\xD9'
PROTOCOL_VERSION = 70016
USER_AGENT = '/minimal-client:0.1/'
HEIGHT = 754565
RELAY = 0

class ConnectionError(Exception):
    pass

class ProtocolError(Exception):
    pass

def sha256(data):
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()


def create_connection(address, timeout, proxy=None):
    if address[0].endswith('.onion'):
        if not proxy:
            raise ConnectionError('Tor proxy is required for .onion addresses.')
        # Use Tor SOCKS5 proxy for .onion addresses
        socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, proxy[0], proxy[1])
        sock = socks.socksocket()
    else:
        # Normal IP address connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    sock.settimeout(timeout)
    sock.connect(address)
    return sock


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

    def open(self):
        self.socket = create_connection(self.to_addr,
                                        self.socket_timeout,
                                        proxy=self.proxy)

    def close(self):
        if self.socket:
            self.socket.close()

    def handshake(self):
        version_msg = serialize_version_msg(self.to_addr, self.from_addr, self.protocol_version, self.user_agent,
                                            self.height, self.relay)
        print(f"Sending handshake data: {version_msg.hex()}")  # Display received data in hex format
        self.send(version_msg)

        # Receive the response (version and verack)
        data = self.receive()
        print(f"Received: {data.hex()}")  # Display received data in hex format

        # Additional message processing could go here (e.g., deserializing the version message)
        version_response = deserialize_version_message(data)
        print(f"Version message received:\n{version_response}")
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
    if address.endswith('.onion') and CONF['onion']:
        proxy = random.choice(CONF['tor_proxies'])

    conn = Connection((address, int(CONF['port'])),
                      (CONF['source_address'], 0),
                      socket_timeout=CONF['socket_timeout'],
                      proxy=proxy)
    try:
        conn.open()
        version_msg = conn.handshake()
    except (ProtocolError, ConnectionError, socket.error) as err:
        logging.error(f'{conn.to_addr}: {err}')
        return None
    except Exception as err:
        logging.error(f'{conn.to_addr}: {err}')
        return None
    if version_msg:
        return version_msg
    return None


# Example usage
CONF = {
    'port': 8333,
    'source_address': '0.0.0.0',
    'socket_timeout': 30,
    'protocol_version': 70016,
    'user_agent': '/minimal-client:0.1/',
    'onion': True,
    'tor_proxies': [('127.0.0.1', 9050)]
}

address = "qd2w2bqttlplyytjfley4wkkuwsliw6lvwpwsfuu4g4qtnmmzslcd5qd.onion"#"64.225.71.231"
version_info = connect(address)
if version_info:
    print(f"Version: {version_info['version']}, User Agent: {version_info['user_agent']}")
