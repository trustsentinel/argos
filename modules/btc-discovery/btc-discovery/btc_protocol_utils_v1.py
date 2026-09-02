import struct
import random
import time
import hashlib
import socket

MAGIC_NUMBER = b'\xF9\xBE\xB4\xD9'
PROTOCOL_VERSION = 70016
USER_AGENT = '/minimal-client:0.1/'
HEIGHT = 754565
RELAY = 0

def sha256(data):
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()

def serialize_version_msg(to_addr, from_addr, protocol_version=PROTOCOL_VERSION, user_agent=USER_AGENT, height=HEIGHT, relay=RELAY):
    payload = struct.pack('<i', protocol_version)  # Version
    payload += struct.pack('<Q', 1)  # Services
    payload += struct.pack('<q', int(time.time()))  # Timestamp

    # Handle the address differently for .onion addresses
    if to_addr[0].endswith('.onion'):
        ipv6_mapped_ipv4 = b'\x00' * 16  # Placeholder for .onion addresses
    else:
        ipv6_mapped_ipv4 = b'\x00' * 10 + b'\xff' * 2 + socket.inet_aton(to_addr[0])  # Normal IPv4

    # Receiving address
    payload += struct.pack("Q16sH", 1, ipv6_mapped_ipv4, to_addr[1])

    # Transmitting address
    payload += struct.pack("Q16sH", 1, socket.inet_aton(from_addr[0]), from_addr[1])

    # Nonce
    payload += struct.pack('<Q', random.getrandbits(64))

    # User agent
    payload += serialize_string(user_agent)

    # Start height
    payload += struct.pack('<i', height)

    # Relay flag
    payload += struct.pack('<?', relay)

    return build_msg(b'version', payload)

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
