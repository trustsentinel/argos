import random
import time
import struct
import logging
import hashlib
import socket
import traceback
import gevent

import socks
from src.bitcoin.serializer import deserialize_msg, serialize_msg, serialize_version_message, deserialize_with_header, \
    serialize_with_header

MAGIC_NUMBER = b'\xF9\xBE\xB4\xD9'
PROTOCOL_VERSION = 70016
USER_AGENT = '/minimal-client:0.1/'
HEIGHT = 754565
RELAY = 0

SOCKET_BUFSIZE = 4096

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

    def build_version_message(self):
        return serialize_with_header(b'version',
            serialize_version_message(self.to_addr, self.from_addr, self.protocol_version, self.user_agent,
                                      self.height, self.relay))
    def handshake(self):
        """Perform the handshake and return the version message."""
        version_msg = self.build_version_message()
        logging.debug(f"Sending handshake data: {version_msg}")
        self.send(version_msg)

        version = None
        gevent.sleep(1)
        try:
            messages = self.get_messages(commands = [b'version', b'verack', b'sendaddrv2'])
            logging.debug(f"Receiving message: {messages}")
            if len(messages) > 0:
                return next(
                    (msg for msg in messages if msg['command'] == b'version'), {})

        except TimeoutError as e:
            logging.error(f"Failed to receive expected message: {e}")
        gevent.sleep(1)
        return version

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

    def get_peers(self, configuration):
        """Send 'getaddr' message and retrieve peers."""

        #self.send_getaddr() # Send the getaddr message

        gevent.sleep(1)
        addr_msgs = self.wait_until(expected_commands=[b'addr'], timeout=120)

        peers = self.parse_addr_msgs(addr_msgs, configuration)
        return peers

    def recv(self, length=0):
        """Receive data from the socket."""
        if length > 0:
            chunks = []
            while length > 0:
                chunk = self.socket.recv(SOCKET_BUFSIZE)
                if not chunk:
                    raise ConnectionError(f'{self.to_addr} closed connection')
                chunks.append(chunk)
                length -= len(chunk)
            return b''.join(chunks)
        else:
            data = self.socket.recv(SOCKET_BUFSIZE)
            if not data:
                raise ConnectionError(f'{self.to_addr} closed connection')
            return data

    def wait_until(self, expected_commands, timeout=30, length=0):
        start_time = time.time()
        msgs = []
        while time.time() - start_time < timeout:
            data = self.recv(length=length)
            logging.debug(f"Receiving data {data}")

            while len(data) > 0:
                try:
                    (msg, data) = deserialize_msg(data)
                except Exception as e:
                    logging.debug(f"Message incomplete: {e}, need more data")
                    # Keep receiving data until we have enough
                    while True:
                        additional_data = self.recv(24)  # Read additional data
                        if not additional_data:
                            raise Exception("Connection closed while waiting for more data.")
                        data += additional_data
                        logging.debug(f"Appending additional data, total length now: {len(data)}")

                        try:
                            (msg, data) = deserialize_msg(data)  # Try again to deserialize
                            logging.debug(f"Successfully deserialized after receiving more data: {msg}")
                            break  # Exit the loop if deserialization succeeds
                        except Exception as e:
                            # If it's still short, continue receiving data
                            logging.debug(f"Still not enough data: {e}, continue receiving")
                            break

            command = msg.get('command')
            logging.debug(f"Received command: {command}\n")
            msgs.append(msg)

            # If one of the expected commands is received, return the messages
            if command in expected_commands:
                logging.debug(f"Expected command {command} received.")
                return msgs

            time.sleep(0.1)  # Prevent a tight loop

        raise TimeoutError(f"Timeout waiting for commands: {expected_commands}")

    def get_messages(self, length=0, commands=None):
        """Receive messages from the connection and filter by command."""
        msgs = []
        data = self.recv(length=length)

        logging.debug(f"Receiving data {data}")
        while len(data) > 0:
            gevent.sleep(0)
            try:
                (msg, data) = deserialize_msg(data)
            except Exception:
                data += self.recv(24)
                msg, data = deserialize_msg(data)

            command = msg.get('command')
            logging.debug(f"Received command: {command}\n")
            if command == b'ping':
                self.send_pong(msg['nonce'])
            elif command == b'version':
                self.send_version_reply(msg['version'])
                self.send_getaddr()
            elif command == b'getheaders':
                self.send_headers()
            msgs.append(msg)
        if len(msgs) > 0 and commands:
            msgs[:] = [m for m in msgs if m.get('command') in commands]
        return msgs

    def send_getaddr(self):
        logging.debug(f"Sending getaddr")
        self.send(serialize_msg(b'getaddr'))

    def send_pong(self, nonce):
        print(f"Sending send_pong: {nonce}")
        self.send(serialize_msg(b'ping', nonce=nonce))

    def send_version_reply(self, version):
        print(f"Sending version {version}")
        self.send(serialize_msg(b'version', version = version))

    def send_headers(self):
        # headers = [{
        #   'version': VERSION,
        #   'prev_block_hash': PREV_BLOCK_HASH,
        #   'merkle_root': MERKLE_ROOT,
        #   'timestamp': TIMESTAMP,
        #   'bits': BITS,
        #   'nonce': NONCE
        # },]
        # [headers] >>>
        print(f"Sending headers")
        self.send(serialize_msg(b'headers', headers=[]))

    def parse_addr_msgs(self, addr_msgs, configuration):
        """Parse 'addr' messages to extract peer information."""
        now = int(time.time())
        peers = set()

        for addr_msg in addr_msgs:
            if 'addr_list' not in addr_msg:
                continue

            for peer in addr_msg['addr_list']:
                logging.info(peer)
                timestamp = peer['timestamp']
                age = now - timestamp
                if age < 0 or age > configuration['max_age']:
                    continue

                address = peer['ipv4'] or peer['ipv6'] or peer['onion']
                port = peer['port'] if peer['port'] > 0 else configuration['port']
                services = peer['services']
                if not address:
                    continue

                peers.add((address, port, services, timestamp))

        return list(peers)


def connect(address, configuration):
    proxy = None

    if address[0].endswith('.onion') and configuration['onion']:
        proxy = random.choice(configuration['tor_proxies'])
    elif address[0].endswith('.i2p') and configuration['i2p']:
        proxy = random.choice(configuration['i2p_proxies'])

    conn = Connection((address[0], int(address[1])),
                      (configuration['source_address'], 0),
                      socket_timeout=configuration['socket_timeout'],
                      proxy=proxy)
    version_msg = None
    try:
        conn.open()
        version_msg = conn.handshake()
        peers = conn.get_peers(configuration)

        return f"Connected {address[0]}:{address[1]} network={conn.network_type}, protocol={conn.protocol}, version={version_msg}, peers={peers}"
    except TimeoutError as err:
        return f"Connected {address[0]}:{address[1]} network={conn.network_type}, protocol={conn.protocol}, version={version_msg}, peers=[]"
    except (ProtocolError, ConnectionError, socket.error) as err:
        traceback.print_exc()
        logging.error(f'{conn.to_addr}: {err}')
        return f"Not connected {address[0]}:{address[1]} network=Unknown, protocol={conn.protocol}, error={str(err)}"
    except Exception as err:
        traceback.print_exc()
        logging.error(f'{conn.to_addr}: {err}')
        return f"Not connected {address[0]}:{address[1]} network=Unknown, protocol={conn.protocol}, error={str(err)}"
    finally:
        conn.close()
