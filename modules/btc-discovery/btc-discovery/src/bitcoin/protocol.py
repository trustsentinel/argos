import base64
import logging
import struct
import random
import time
import hashlib
import socket
import json
from binascii import hexlify
from io import BytesIO

MAGIC_NUMBER = b'\xF9\xBE\xB4\xD9'
PROTOCOL_VERSION = 70016
USER_AGENT = '/minimal-client:0.1/'
HEIGHT = 754565
RELAY = 0
HEADER_LEN = 24

def sha256(data):
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()


def getaddr(self):
    """Send a 'getaddr' message to the connected peer."""
    payload = b''
    msg = self.build_msg(b'getaddr', payload)
    self.send(msg)


def get_messages(self, length=0, commands=None):
    """Receive messages from the connection and filter by command."""
    msgs = []
    data = self.receive(length=length)

    while len(data) > 0:
        try:
            msg, data = self.serializer.deserialize_msg(data)
            logging.debug(f"received {msg} {data}")
        except Exception as err:
            data += self.receive(length=self.serializer.required_len - len(data))
            msg, data = self.serializer.deserialize_msg(data)

        if msg.get('command') == b'ping':
            self.pong(msg['nonce'])  # Respond to ping immediately.
        elif msg.get('command') == b'version':
            self.version_reply(msg)  # Respond to version immediately.
        elif msg.get('command') == b'getheaders':
            self.headers([])  # Respond to getheaders immediately.

        msgs.append(msg)

    if msgs and commands:
        msgs[:] = [m for m in msgs if m.get('command') in commands]
    return msgs




def deserialize_header(self, data):
    """Deserialize the message header."""
    data = BytesIO(data)
    msg = {
        'magic_number': data.read(4),
        'command': data.read(12).strip(b'\x00'),
        'length': struct.unpack('<I', data.read(4))[0],
        'checksum': data.read(4)
    }

    if msg['magic_number'] != self.magic_number:
        raise Exception(
            f"not valid magic number {hexlify(msg['magic_number'])} != {hexlify(self.magic_number)}"
        )

    return msg

def bytes_to_base64(obj):
    if isinstance(obj, bytes):
        return base64.b64encode(obj).decode('utf-8')
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def bytes_to_list(obj):
    """Custom JSON encoder to convert bytes to a list of integers."""
    if isinstance(obj, bytes):
        return list(obj)  # Convert bytes to a list of integers
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

def list_to_bytes(dct):
    """Custom JSON decoder to convert lists of integers back to bytes."""
    return {k: (bytes(v) if isinstance(v, list) else v) for k, v in dct.items()}


def build_msg(command, data):
    length = len(data)
    checksum = sha256(data)[:4]
    msg = [
        MAGIC_NUMBER,
        command + b'\x00' * (12 - len(command)),
        struct.pack('<I', length),
        checksum,
        data
    ]
    return b''.join(msg)

def serialize_string(string):
    data = string.encode()
    return struct.pack('<B', len(data)) + data

def deserialize_version_message(data):
    msg = {}
    stream = BytesIO(data)

    msg['version'] = struct.unpack('<i', stream.read(4))[0]
    msg['services'] = struct.unpack('<Q', stream.read(8))[0]
    msg['timestamp'] = struct.unpack('<q', stream.read(8))[0]

    recv_services = struct.unpack('<Q', stream.read(8))[0]
    recv_ip = stream.read(16)
    recv_port = struct.unpack('>H', stream.read(2))[0]

    trans_services = struct.unpack('<Q', stream.read(8))[0]
    trans_ip = stream.read(16)
    trans_port = struct.unpack('>H', stream.read(2))[0]

    msg['nonce'] = struct.unpack('<Q', stream.read(8))[0]

    user_agent_len = struct.unpack('B', stream.read(1))[0]
    msg['user_agent'] = stream.read(user_agent_len).decode()

    msg['height'] = struct.unpack('<i', stream.read(4))[0]

    try:
        msg['relay'] = struct.unpack('<?', stream.read(1))[0]
    except struct.error:
        msg['relay'] = None

    return msg