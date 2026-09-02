import random
import struct
import logging
import socket
import traceback

import socks

import btc_protocol
from serialization import sha256

MAGIC_NUMBER = b'\xF9\xBE\xB4\xD9'
PROTOCOL_VERSION = 70016
USER_AGENT = '/minimal-client:0.1/'
HEIGHT = 754565
RELAY = 0

class ConnectionError(Exception):
    pass

class ProtocolError(Exception):
    pass


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

class BtcConnection:
    def __init__(self, to_addr, from_addr, proxy = None, **conf):
        self.to_addr = to_addr
        self.from_addr = from_addr
        self.protocol_version = conf.get('protocol_version', PROTOCOL_VERSION)
        self.user_agent = conf.get('user_agent', USER_AGENT)
        self.height = conf.get('height', HEIGHT)
        self.relay = conf.get('relay', RELAY)
        self.socket_timeout = conf.get('socket_timeout', 30)
        self.proxy = proxy
        self.socket = None

    def open(self):
        self.socket = create_connection(self.to_addr,
                                        self.socket_timeout,
                                        proxy=self.proxy)

    def close(self):
        if self.socket:
            self.socket.close()

    def build_msg(self, command, payload):
        length = len(payload)
        checksum = sha256(payload)[:4]
        msg = [
            MAGIC_NUMBER,
            command + b'\x00' * (12 - len(command)),
            struct.pack('<I', length),
            checksum,
            payload
        ]
        return b''.join(msg)

    def handshake(self):
        version_msg = btc_protocol.create_version_message(self.to_addr[0])
        self.send(version_msg)

        data = self.receive()
        print(f"Received: {data.hex()}")

        version_response = btc_protocol.deserialize_version_message(data)
        print(f"Version message received:\n{version_response}")
        return version_response

    def send(self, msg):
        self.socket.sendall(msg)

    def receive(self):
        header = self.socket.recv(24)
        if len(header) < 24:
            raise ValueError('Incomplete header received')

        payload_length = struct.unpack('<I', header[16:20])[0]
        payload = self.socket.recv(payload_length)
        while len(payload) < payload_length:
            payload += self.socket.recv(payload_length - len(payload))

        return payload


def connect(address):
    proxy = None
    if address.endswith('.onion') and CONF['onion']:
        proxy = random.choice(CONF['tor_proxies'])

    conn = BtcConnection((address, int(CONF['port'])),
                      (CONF['source_address'], 0),
                      proxy)
    try:
        conn.open()
        version_msg = conn.handshake()
    except (ProtocolError, ConnectionError, socket.error) as err:
        logging.debug(f'{conn.to_addr}: {err}')
        return None
    except Exception as err:
        traceback.print_exc()
        logging.error(f'{conn.to_addr}: {err}')
        return None

    if version_msg:
        return version_msg
    return None


CONF = {
    'port': 8333,
    'source_address': '0.0.0.0',
    'socket_timeout': 30,
    'protocol_version': 70016,
    'user_agent': '/minimal-client:0.1/'
}

address = "64.225.71.231"
version_info = connect(address)
if version_info:
    print(f"Version: {version_info['version']}, User Agent: {version_info['user_agent']}")
