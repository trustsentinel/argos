# Reserved network IDs.
import hashlib
from base64 import b32encode

NETWORK_IPV4 = 1
NETWORK_IPV6 = 2
NETWORK_TORV2 = 3
NETWORK_TORV3 = 4
NETWORK_I2P = 5
NETWORK_CJDNS = 6
# IPv6 prefix for .onion address (use in addr message only).
ONION_PREFIX = b'\xFD\x87\xD8\x7E\xEB\x43'
NETWORK_LENGTHS = {
    NETWORK_IPV4: 4,
    NETWORK_IPV6: 16,
    NETWORK_TORV2: 10,
    NETWORK_TORV3: 32,
    NETWORK_I2P: 32,
    NETWORK_CJDNS: 16,
}

SUPPORTED_NETWORKS = [
    NETWORK_IPV4,
    NETWORK_IPV6,
    NETWORK_TORV2,
    NETWORK_TORV3,
]

def addr_to_onion_v2(addr):
    """
    Returns .onion address for the specified v2 onion addr.
    """
    return (b32encode(addr).lower() + b'.onion').decode()


def addr_to_onion_v3(addr):
    """
    Returns .onion address for the specified v3 onion addr (PUBKEY).

    onion_address = base32(PUBKEY | CHECKSUM | VERSION) + '.onion'
    See https://gitweb.torproject.org/torspec.git/tree/rend-spec-v3.txt#n2135
    """
    version = b'\x03'
    checksum = hashlib.sha3_256(
        b'.onion checksum' + addr + version).digest()[:2]
    return (b32encode(addr + checksum + version).lower() + b'.onion').decode()

