import traceback

from dns import resolver, reversename
import socket
import asyncio
import concurrent.futures

# Connect to a dns address and get the A records
# The IP address and port is at index [4][0]
# for example: ('13.250.46.106', 8333)
async def get_addresses(address, port, timeout=10):
    loop = asyncio.get_running_loop()
    try:
        with concurrent.futures.ThreadPoolExecutor() as pool:
            addresses = await asyncio.wait_for(
                loop.run_in_executor(
                    pool,
                    lambda: socket.getaddrinfo(
                        address, port, socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP
                    )
                ),
                timeout=timeout  # Apply the timeout here
            )
        return [(info[4][0], info[4][1]) for info in addresses]
    except concurrent.futures.TimeoutError:
        print(f"Timeout reached while trying to resolve {address}:{port}")
        return []
    except Exception as err:
        print(f"Error occurred: {err}")
        return []


async def resolve_address(ip):
    try:
        n = reversename.from_address(ip)
        result = resolver.resolve(n, 'PTR')
        for val in result:
            return val.to_text()
    except Exception as err:
        return None
    return None
