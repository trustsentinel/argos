import random
import time
import struct
import logging
import hashlib
import socket
from io import BytesIO


def serialize_version_msg(protocol_version, to_address, from_address, user_agent, height, relay):
    payload = struct.pack('<i', self.protocol_version)
    payload += struct.pack('<Q', 1)
    payload += struct.pack('<q', int(time.time()))
    payload += struct.pack('<Q', 1) + socket.inet_aton(self.to_addr[0]) + struct.pack('>H', self.to_addr[1])
    payload += struct.pack('<Q', 1) + socket.inet_aton(self.from_addr[0]) + struct.pack('>H', self.from_addr[1])
    payload += struct.pack('<Q', random.getrandbits(64))
    payload += self.serialize_string(self.user_agent)
    payload += struct.pack('<i', self.height)
    payload += struct.pack('<?', self.relay)
    return self.build_msg(b'version', payload)

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

def create_version_message(host):
    version = struct.pack("i", 70015)
    services = struct.pack("Q", 0)
    timestamp = struct.pack("q", int(time.time()))
    ipv6_mapped_ipv4 = b'\x00' * 10 + b'\xff' * 2 + socket.inet_aton(host)
    add_recv = struct.pack("Q16sH", 0, ipv6_mapped_ipv4, 8333)
    add_trans = struct.pack("Q16sH", 0, ipv6_mapped_ipv4, 8333)
    nonce = struct.pack("Q", random.getrandbits(64))
    user_agent = struct.pack("B", 0)
    height = struct.pack("i", 525453)
    relay = struct.pack("?", False)
    payload = version + services + timestamp + add_recv + add_trans + nonce + user_agent + height + relay

    magic_bytes = bytes.fromhex("F9BEB4D9")
    command = b"version" + b"\x00" * (12 - len("version"))
    length = struct.pack("I", len(payload))
    checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]

    header = magic_bytes + command + length + checksum
    return header + payload
