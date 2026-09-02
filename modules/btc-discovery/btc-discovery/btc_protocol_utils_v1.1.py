import base64
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


def get_address_bytes(addr):
    """
    Auxiliary method to handle IPv4, IPv6, IPv6-mapped IPv4, .onion, and .i2p addresses.
    Returns the 16-byte address representation.
    """
    if addr[0].endswith('.onion'):
        # Handle .onion address (Tor)
        onion_address = addr[0].replace('.onion', '')
        # Decode the Base32 onion address
        onion_bytes = base64.b32decode(onion_address.upper())  # .onion addresses are Base32
        return b'\x00' * 6 + b'\xfd' + onion_bytes[:10]  # Tor v2/v3 use first 10 bytes, with prefix

    elif addr[0].endswith('.i2p'):
        # Handle .i2p address (I2P)
        i2p_address = addr[0].replace('.i2p', '')
        i2p_bytes = hashlib.sha256(i2p_address.encode()).digest()[:16]  # Use SHA-256 hash truncated to 16 bytes
        return i2p_bytes

    try:
        # Check if it's a valid IPv6 address
        socket.inet_pton(socket.AF_INET6, addr[0])
        if addr[0].startswith('::ffff:'):
            # It's an IPv6-mapped IPv4 address (e.g., ::ffff:192.168.1.1)
            # Convert the hexadecimal part back to IPv4 dotted decimal format
            ipv4_hex = addr[0].split(':')[-2:]  # Get the last two parts ('40e1', '47e7')
            # Convert each part of the hex to decimal bytes (2 bytes for each)
            ipv4_bytes = bytes.fromhex(ipv4_hex[0]) + bytes.fromhex(ipv4_hex[1])
            ipv4 = '.'.join(map(str, ipv4_bytes))  # Convert each byte to decimal and join with '.'

            # Now convert the final IPv4 string to bytes
            ipv4_bytes = socket.inet_aton(ipv4)
            ipv6_mapped_ipv4 = b'\x00' * 10 + b'\xff' * 2 + ipv4_bytes
        else:
            # It's a pure IPv6 address
            ipv6_mapped_ipv4 = socket.inet_pton(socket.AF_INET6, addr[0])
    except socket.error:
        # It's an IPv4 address
        ipv4_bytes = socket.inet_aton(addr[0])
        ipv6_mapped_ipv4 = b'\x00' * 10 + b'\xff' * 2 + ipv4_bytes

    return ipv6_mapped_ipv4


def serialize_version_msg(to_addr, from_addr, protocol_version=PROTOCOL_VERSION, user_agent=USER_AGENT, height=HEIGHT, relay=RELAY):
    payload = struct.pack('<i', protocol_version)  # Version
    payload += struct.pack('<Q', 1)  # Services
    payload += struct.pack('<q', int(time.time()))  # Timestamp

    to_addr_bytes = get_address_bytes(to_addr)
    from_addr_bytes = get_address_bytes(from_addr)

    # Receiving address (services + IP address + port)
    payload += struct.pack('Q', 1) + to_addr_bytes + struct.pack('>H', to_addr[1])
    # Sending address (services + IP address + port)
    payload += struct.pack('Q', 1) + from_addr_bytes + struct.pack('>H', from_addr[1])

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
