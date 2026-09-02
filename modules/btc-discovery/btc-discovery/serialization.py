import hashlib
import struct

def sha256(data):
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()

def serialize_string(string):
    data = string.encode()
    return struct.pack('<B', len(data)) + data