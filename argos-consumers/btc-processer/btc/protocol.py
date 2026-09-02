import socket
import struct
import time
import random
import hashlib
import socket
import struct
import time
import random
import hashlib
import traceback



def create_version_message(host):
    version = struct.pack("i", 70015)
    services = struct.pack("Q", 0)
    timestamp = struct.pack("q", int(time.time()))
    add_recv = struct.pack("Q16sH", 0, bytes(host, 'utf-8'), 8333)
    add_trans = struct.pack("Q16sH", 0, bytes("127.0.0.1", 'utf-8'), 8333)
    nonce = struct.pack("Q", random.getrandbits(64))
    user_agent = struct.pack("B", 0)
    height = struct.pack("i", 525453)
    relay = struct.pack("?", False)
    payload = version + services + timestamp + add_recv + add_trans + nonce + user_agent + height + relay
    header = bytes.fromhex("F9BEB4D9") + b"version" + 5 * b"\00" + struct.pack("I", len(payload)) + hashlib.sha256(
        hashlib.sha256(payload).digest()).digest()[:4]
    return header + payload


def get_node_services(services):
    flags = [1 << i for i in [0, 1, 2, 3, 10]]
    return [bool(services & flag) for flag in flags]


def encode_received_message(recv_message):
    recv_payload = recv_message[24:]
    recv_version = struct.unpack("i", recv_payload[:4])
    recv_services = struct.unpack("<Q", recv_payload[4:12])[0]
    service_flags = get_node_services(recv_services)
    # print(f"NODE_NETWORK: {service_flags[0]}")
    # print(f"NODE_GETUTXO: {service_flags[1]}")
    # print(f"NODE_BLOOM: {service_flags[2]}")
    # print(f"NODE_WITNESS: {service_flags[3]}")
    # print(f"NODE_NETWORK_LIMITED: {service_flags[4]}")
    return [recv_version, service_flags]


async def connect_and_get_version(host, port, public_key=None):
    print(f"bitcoin.handshake | connecting to a btc peer: {host}:{port}")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    try:
        sock.connect((host, port))
        sock.send(create_version_message(host))
        time.sleep(1)
        start_time = time.time()
        [version, flags] = encode_received_message(sock.recv(8192))
        latency = time.time() - start_time

        print(f"bitcoin.handshake | peer: {host}:{port}, latency: {latency} seconds")
        print(f"bitcoin.handshake | peer: {host}:{port}, version: {version[0]}")
    except socket.timeout:
        return {
            "error": "NETWORK",
            "reason": f"Timeout connecting to peer {host}:{port}"
        }
    except Exception as e:
        return {
            "error": "INTERNAL",
            "reason": traceback.format_exc()
        }
    finally:
        sock.close()

    return {
        "version": version[0],
        "network_type": flags[0],
        "network_utxo": flags[1],
        "network_bloom": flags[2],
        "network_witness": flags[3],
        "network_limited": flags[4],
    }

