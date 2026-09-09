"""A minimal fake Bitcoin node for the end-to-end test.

It listens on :8333 and, on every connection, sends back a well-formed
`version` message (24-byte header + version + services) so the btc-processer's
`connect_and_get_version()` probe completes deterministically — no live
internet and no real peer required.
"""
import hashlib
import socket
import struct
import threading


def build_version_response() -> bytes:
    # payload: protocol version (int32 LE) + services (uint64 LE, NODE_NETWORK)
    payload = struct.pack("<i", 70015) + struct.pack("<Q", 1)
    magic = b"\xf9\xbe\xb4\xd9"
    command = b"version" + b"\x00" * 5  # 12 bytes
    length = struct.pack("<I", len(payload))
    checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    header = magic + command + length + checksum  # 24 bytes
    return header + payload


RESPONSE = build_version_response()


def handle(conn: socket.socket) -> None:
    try:
        conn.sendall(RESPONSE)
        conn.settimeout(2)
        try:
            conn.recv(4096)  # drain the client's own version message
        except OSError:
            pass
    finally:
        conn.close()


def main() -> None:
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("0.0.0.0", 8333))
    srv.listen(50)
    print("mock-btc: listening on :8333", flush=True)
    while True:
        conn, _ = srv.accept()
        threading.Thread(target=handle, args=(conn,), daemon=True).start()


if __name__ == "__main__":
    main()
