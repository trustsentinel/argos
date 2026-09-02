import base64
import hashlib
import logging
import random
import socket
import struct
import time
from binascii import hexlify, unhexlify
from io import BytesIO

from src.bitcoin.addresses import NETWORK_LENGTHS, SUPPORTED_NETWORKS, NETWORK_TORV2, NETWORK_TORV3, NETWORK_IPV6, \
    NETWORK_IPV4, addr_to_onion_v2, addr_to_onion_v3, ONION_PREFIX

HEADER_LEN = 24
MAGIC_NUMBER = b'\xF9\xBE\xB4\xD9'
PROTOCOL_VERSION = 70016
USER_AGENT = '/minimal-client:0.1/'
HEIGHT = 754565
RELAY = 0
HEADER_LEN = 24

def sha256(data):
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()

def serialize_with_header(command, data):
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

def deserialize_with_header(data):
    data = BytesIO(data)
    return {
        'magic_number': data.read(4),
        'command': data.read(12).strip(b'\x00'),
        'length': struct.unpack('<I', data.read(4))[0],
        'checksum': data.read(4)
    }

def serialize_msg(command, **kwargs):
    if command == b'version':
        return serialize_version_replay_message(kwargs['version'])
    elif command == b'ping' or command == b'pong':
        return serialize_pong_msg(kwargs['nonce'])
    elif command == b'sendaddr2':
        return serialize_sendaddr2_msg()
    elif command == b'getaddr':
        return serialize_getaddr_msg()
    elif command == b'headers':
        return serialize_headers_message(kwargs['headers'])
    return serialize_unknown(command)

def serialize_sendaddr2_msg():
    return serialize_with_header(b'sendaddr2', b'')

def serialize_pong_msg(nonce):
    return serialize_with_header(b'ping', struct.pack('<Q', nonce))

def serialize_getaddr_msg():
    return serialize_with_header(b'getaddr', b'')

def serialize_version_replay_message(version):
    if version >= 70016:
        return serialize_sendaddrv2_msg() \
              + serialize_verack_msg()
    return serialize_verack_msg()

def serialize_sendaddrv2_msg():
    return serialize_with_header(b'sendaddrv2', b'')

def serialize_verack_msg():
    return serialize_with_header(b'verack', b'')

def serialize_block_header(header):
    payload = [
        struct.pack('<I', header['version']),
        unhexlify(header['prev_block_hash'])[::-1],  # LE -> BE
        unhexlify(header['merkle_root'])[::-1],  # LE -> BE
        struct.pack('<I', header['timestamp']),
        struct.pack('<I', header['bits']),
        struct.pack('<I', header['nonce']),
        serialize_int(0),
    ]
    return b''.join(payload)

def serialize_int(length):
    if length < 0xFD:
        return chr(length).encode()
    elif length <= 0xFFFF:
        return chr(0xFD).encode() + struct.pack('<H', length)
    elif length <= 0xFFFFFFFF:
        return chr(0xFE).encode() + struct.pack('<I', length)
    return chr(0xFF).encode() + struct.pack('<Q', length)

def serialize_headers_message(headers):
    payload = [
        serialize_int(len(headers)),
    ]
    payload.extend(
        [serialize_block_header(header) for header in headers])

    return serialize_with_header(b'headers', b''.join(payload))

def serialize_unknown(command):
    return serialize_with_header(command,  b'')

def serialize_string(string):
    data = string.encode()
    return struct.pack('<B', len(data)) + data

def serialize_version_message(to_addr, from_addr, protocol_version=PROTOCOL_VERSION, user_agent=USER_AGENT, height=HEIGHT, relay=RELAY):
    payload = struct.pack('<i', protocol_version)  # Version
    payload += struct.pack('<Q', 1)  # Services
    payload += struct.pack('<q', int(time.time()))  # Timestamp

    # Handle the address differently for .onion addresses
    if to_addr[0].endswith('.onion'):
        onion_address = to_addr[0].replace('.onion', '')
        # Decode the Base32 onion address
        onion_bytes = base64.b32decode(onion_address.upper())  # .onion addresses are Base32
        # return b'\x00' * 6 + b'\xfd' + onion_bytes[:10]
        # ipv6_mapped_ipv4 = b'\x00' * 16  # Placeholder for .onion addresses
        ipv6_mapped_ipv4 = b'\x00' * 6 + b'\xfd' + onion_bytes[:10]
    else:
        ipv6_mapped_ipv4 = b'\x00' * 10 + b'\xff' * 2 + socket.inet_aton(to_addr[0])  # Normal IPv4

    # Receiving address
    payload += struct.pack("Q16sH", 1, ipv6_mapped_ipv4, to_addr[1])

    # Transmitting address
    payload += struct.pack("Q16sH", 1, socket.inet_aton(from_addr[0]), from_addr[1])

    # Nonce
    nonce = random.getrandbits(64)
    payload += struct.pack('<Q', nonce)

    # User agent
    user_agent_str = serialize_string(user_agent)
    payload += user_agent_str

    # Start height
    payload += struct.pack('<i', height)

    # Relay flag
    payload += struct.pack('<?', relay)
    return payload

def deserialize_msg(data):
    msg = {}
    data_len = len(data)

    if data_len < HEADER_LEN:
        raise Exception(f'too short header got {data_len} of {HEADER_LEN} bytes')

    data = BytesIO(data)
    header = data.read(HEADER_LEN)

    header_deserialized = deserialize_with_header(header)
    logging.debug(f"...Header: {header_deserialized}")
    msg.update(deserialize_with_header(header))

    if (data_len - HEADER_LEN) < msg['length']:
        required_len = HEADER_LEN + msg['length']
        raise Exception(f'payload short got {data_len} of {required_len} bytes')

    payload = data.read(msg['length'])
    logging.debug(f"...Payload: {payload}")

    computed_checksum = sha256(sha256(payload))[:4]

    #if computed_checksum != msg['checksum']:
    #    raise Exception(f"chksum not valid {hexlify(computed_checksum)} != {hexlify(msg['checksum'])}")

    msg.update(deserialize(msg['command'], payload))
    return (msg, data.read())

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

def deserialize_ping_message(data):
    return {
        'nonce': struct.unpack('<Q', BytesIO(data).read(8))[0],
    }

def deserialize_unknown(data):
    msg = {}
    stream = BytesIO(data)
    return msg

def deserialize_int(data):
    length = struct.unpack('<B', data.read(1))[0]
    if length == 0xFD:
        length = struct.unpack('<H', data.read(2))[0]
    elif length == 0xFE:
        length = struct.unpack('<I', data.read(4))[0]
    elif length == 0xFF:
        length = struct.unpack('<Q', data.read(8))[0]
    return length


def deserialize_network_address(data, has_timestamp=False,
                                version=None):
    network_id = 0
    ipv4 = ''
    ipv6 = ''
    onion = ''

    timestamp = None
    if has_timestamp:
        timestamp = struct.unpack('<I', data.read(4))[0]

    if version == 2:
        services = deserialize_int(data)

        network_id = struct.unpack('<B', data.read(1))[0]

        if network_id not in NETWORK_LENGTHS.keys():
            raise Exception(f'unknown network id {network_id}')

        if network_id not in SUPPORTED_NETWORKS:
            raise Exception(
                f'unsupported network id {network_id}')

        addr_len = deserialize_int(data)
        if addr_len != NETWORK_LENGTHS[network_id]:
            raise Exception

        addr = data.read(addr_len)
        if network_id == NETWORK_TORV2:
            onion = addr_to_onion_v2(addr)
        elif network_id == NETWORK_TORV3:
            onion = addr_to_onion_v3(addr)
        elif network_id == NETWORK_IPV6:
            ipv6 = socket.inet_ntop(socket.AF_INET6, addr)
        elif network_id == NETWORK_IPV4:
            ipv4 = socket.inet_ntop(socket.AF_INET, addr)

        port = struct.unpack('>H', data.read(2))[0]
    else:
        services = struct.unpack('<Q', data.read(8))[0]

        _ipv6 = data.read(12)
        _ipv4 = data.read(4)

        port = struct.unpack('>H', data.read(2))[0]

        _ipv6 += _ipv4
        if _ipv6[:6] == ONION_PREFIX:
            onion = addr_to_onion_v2(_ipv6[6:])  # Use .onion
            network_id = NETWORK_TORV2
        else:
            ipv6 = socket.inet_ntop(socket.AF_INET6, _ipv6)
            ipv4 = socket.inet_ntop(socket.AF_INET, _ipv4)
            if ipv4 in ipv6:
                ipv6 = ''  # Use IPv4
                network_id = NETWORK_IPV4
            else:
                ipv4 = ''  # Use IPv6
                network_id = NETWORK_IPV6

    return {
        'network_id': network_id,
        'timestamp': timestamp,
        'services': services,
        'ipv4': ipv4,
        'ipv6': ipv6,
        'onion': onion,
        'port': port,
    }
def deserialize_addr_message(data, version=None):
    msg = {}
    data = BytesIO(data)

    msg['count'] = deserialize_int(data)
    msg['addr_list'] = []
    for _ in range(msg['count']):
        network_address = deserialize_network_address(
            data, has_timestamp=True, version=version)
        msg['addr_list'].append(network_address)

    return msg

def deserialize(command, data):
    if command == b'version':
        return deserialize_version_message(data)
    elif command == b'ping' or command == b'pong':
        return deserialize_ping_message(data)
    if command == b'addr':
        return deserialize_addr_message(data)
    return deserialize_unknown(data)
