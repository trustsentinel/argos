"""Unit tests for the pure Bitcoin wire-protocol helpers."""
import hashlib
import struct

from btc.protocol import (
    create_version_message,
    encode_received_message,
    get_node_services,
)


def test_get_node_services_node_network_only():
    # services bitfield = 1 -> only NODE_NETWORK (bit 0) set
    assert get_node_services(1) == [True, False, False, False, False]


def test_get_node_services_witness_bit():
    # bit 3 (value 8) = NODE_WITNESS
    assert get_node_services(8) == [False, False, False, True, False]


def test_create_version_message_header_is_well_formed():
    msg = create_version_message("1.2.3.4")
    assert msg[:4] == bytes.fromhex("F9BEB4D9")   # mainnet magic bytes
    assert msg[4:11] == b"version"                 # command field

    payload = msg[24:]
    declared_len = struct.unpack("<I", msg[16:20])[0]
    assert declared_len == len(payload)            # length header matches payload

    checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    assert msg[20:24] == checksum                  # double-SHA256 checksum matches


def test_encode_received_message_parses_version_and_services():
    payload = struct.pack("<i", 70015) + struct.pack("<Q", 1)
    recv = b"\x00" * 24 + payload  # 24-byte header we skip, then the payload
    version, flags = encode_received_message(recv)
    assert version[0] == 70015
    assert flags[0] is True        # NODE_NETWORK advertised
