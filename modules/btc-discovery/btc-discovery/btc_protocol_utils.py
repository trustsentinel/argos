import base64
import logging
import struct
import random
import time
import hashlib
import socket
import json

MAGIC_NUMBER = b'\xF9\xBE\xB4\xD9'
PROTOCOL_VERSION = 70016
USER_AGENT = '/minimal-client:0.1/'
HEIGHT = 754565
RELAY = 0

def sha256(data):
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()

def serialize_version_msg(to_addr, from_addr, protocol_version=PROTOCOL_VERSION, user_agent=USER_AGENT, height=HEIGHT, relay=RELAY):
    version = {}
    payload = struct.pack('<i', protocol_version)  # Version
    version["protocol_version"] = protocol_version
    payload += struct.pack('<Q', 1)  # Services
    version["services"] = 1
    payload += struct.pack('<q', int(time.time()))  # Timestamp
    version["timestamp"] = int(time.time())

    # Handle the address differently for .onion addresses
    if to_addr[0].endswith('.onion'):
        onion_address = to_addr[0].replace('.onion', '')
        # Decode the Base32 onion address
        onion_bytes = base64.b32decode(onion_address.upper())  # .onion addresses are Base32
        #return b'\x00' * 6 + b'\xfd' + onion_bytes[:10]
        #ipv6_mapped_ipv4 = b'\x00' * 16  # Placeholder for .onion addresses
        ipv6_mapped_ipv4 = b'\x00' * 6 + b'\xfd' + onion_bytes[:10]
    else:
        ipv6_mapped_ipv4 = b'\x00' * 10 + b'\xff' * 2 + socket.inet_aton(to_addr[0])  # Normal IPv4


    # Receiving address
    payload += struct.pack("Q16sH", 1, ipv6_mapped_ipv4, to_addr[1])
    version["receiving_address"] = ipv6_mapped_ipv4

    # Transmitting address
    payload += struct.pack("Q16sH", 1, socket.inet_aton(from_addr[0]), from_addr[1])
    version["destination_address"] = socket.inet_aton(from_addr[0])

    # Nonce
    nonce = random.getrandbits(64)
    payload += struct.pack('<Q', nonce)
    version["nonce"] = nonce

    # User agent
    user_agent_str = serialize_string(user_agent)
    payload += user_agent_str
    version["user_agent"] = user_agent_str

    # Start height
    payload += struct.pack('<i', height)
    version["height"] = height

    # Relay flag
    payload += struct.pack('<?', relay)
    version["relay"] = relay

    logging.debug(f"Sending version packet: {json.dumps(version, default=bytes_to_list)}")
    return build_msg(b'version', payload)

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


def build_msg(command, payload):
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

def serialize_string(string):
    data = string.encode()
    return struct.pack('<B', len(data)) + data
