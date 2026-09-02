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


def deserialize_version_message(data):
    # Start reading from the payload portion
    msg = {}
    stream = BytesIO(data)

    # Version (int32, little-endian)
    msg['version'] = struct.unpack('<i', stream.read(4))[0]

    # Services (uint64, little-endian)
    msg['services'] = struct.unpack('<Q', stream.read(8))[0]

    # Timestamp (int64, little-endian)
    msg['timestamp'] = struct.unpack('<q', stream.read(8))[0]

    # Receiving address (services (uint64) + IPv6-mapped IPv4 (16 bytes) + port (uint16, big-endian))
    recv_services = struct.unpack('<Q', stream.read(8))[0]
    recv_ip = stream.read(16)  # IPv6-mapped IPv4 address
    recv_port = struct.unpack('>H', stream.read(2))[0]  # Port is big-endian

    # Transmitting address (services (uint64) + IPv6-mapped IPv4 (16 bytes) + port (uint16, big-endian))
    trans_services = struct.unpack('<Q', stream.read(8))[0]
    trans_ip = stream.read(16)  # IPv6-mapped IPv4 address
    trans_port = struct.unpack('>H', stream.read(2))[0]  # Port is big-endian

    # Nonce (uint64, little-endian)
    msg['nonce'] = struct.unpack('<Q', stream.read(8))[0]

    # User agent (variable length string)
    user_agent_len = struct.unpack('B', stream.read(1))[0]  # Length of user agent string
    msg['user_agent'] = stream.read(user_agent_len).decode()  # User agent string

    # Start height (int32, little-endian)
    msg['height'] = struct.unpack('<i', stream.read(4))[0]

    # Relay (boolean, only exists if protocol version >= 70001)
    try:
        msg['relay'] = struct.unpack('<?', stream.read(1))[0]
    except struct.error:
        msg['relay'] = None  # Relay flag might be missing if version < 70001

    return msg

def create_version_message(host):
    version = struct.pack("i", 70015)  # Protocol version 70015
    services = struct.pack("Q", 0)  # Node services (set to 0)
    timestamp = struct.pack("q", int(time.time()))  # Current timestamp
    # Format IP address and port in IPv6-mapped IPv4 format
    ipv6_mapped_ipv4 = b'\x00' * 10 + b'\xff' * 2 + socket.inet_aton(host)
    add_recv = struct.pack("Q16sH", 0, ipv6_mapped_ipv4, 8333)  # Address of receiving node
    add_trans = struct.pack("Q16sH", 0, ipv6_mapped_ipv4, 8333)  # Address of transmitting node
    nonce = struct.pack("Q", random.getrandbits(64))  # Random nonce
    user_agent = struct.pack("B", 0)  # User agent string length (empty for now)
    height = struct.pack("i", 525453)  # Blockchain height (set arbitrarily)
    relay = struct.pack("?", False)  # Do not relay transactions
    payload = version + services + timestamp + add_recv + add_trans + nonce + user_agent + height + relay

    # Message header: [Magic bytes (4)] + [Command ("version")] + [Length of payload (4)] + [Checksum (4)]
    magic_bytes = bytes.fromhex("F9BEB4D9")  # Mainnet magic bytes
    command = b"version" + b"\x00" * (12 - len("version"))  # "version" padded to 12 bytes
    length = struct.pack("I", len(payload))  # Payload length
    checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]  # First 4 bytes of double SHA256 checksum

    # Construct and return full message
    header = magic_bytes + command + length + checksum
    return header + payload

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
    if address[0].endswith('.onion') and not proxy:
        raise ConnectionError('Tor proxy is required for .onion addresses.')

    if proxy:
        socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, proxy[0], proxy[1])
        sock = socks.socksocket()
    else:
        sock = socket.socket()

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
        self.socket = create_connection(self.to_addr, self.socket_timeout, proxy=self.proxy)

    def close(self):
        if self.socket:
            self.socket.close()

    def serialize_version_msg(self):
        payload = struct.pack('<i', self.protocol_version)  # Version
        payload += struct.pack('<Q', 1)  # Services
        payload += struct.pack('<q', int(time.time()))  # Timestamp
        payload += struct.pack('<Q', 1) + socket.inet_aton(self.to_addr[0]) + struct.pack('>H',
                                                                                          self.to_addr[1])  # Addr_recv
        payload += struct.pack('<Q', 1) + socket.inet_aton(self.from_addr[0]) + struct.pack('>H', self.from_addr[
            1])  # Addr_from
        payload += struct.pack('<Q', random.getrandbits(64))  # Nonce
        payload += self.serialize_string(self.user_agent)  # User agent
        payload += struct.pack('<i', self.height)  # Start height
        payload += struct.pack('<?', self.relay)  # Relay flag
        return self.build_msg(b'version', payload)

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

    def serialize_string(self, string):
        data = string.encode()
        return struct.pack('<B', len(data)) + data



    def deserialize_message(self, data):
        # In this example, we are only handling "version" messages
        return deserialize_version_message(data)

    def handshake(self):
        version_msg = create_version_message(self.to_addr[0])
        self.send(version_msg)

        # Receive the response (version and verack)
        data = self.receive()
        print(f"Received: {data.hex()}")  # Display received data in hex format

        # Additional message processing could go here (e.g., deserializing the version message)

        version_response = self.deserialize_message(data)
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
        logging.debug(f'{conn.to_addr}: {err}')
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

address = "sgvi7z7ka6hajteud52trsj3y4yqeeuemeupc2sw5z6iabu2rmlfnkad.onion"#"64.225.71.231"
version_info = connect(address)
if version_info:
    print(f"Version: {version_info['version']}, User Agent: {version_info['user_agent']}")
