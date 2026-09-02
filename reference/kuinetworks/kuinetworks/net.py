import socket

async def get_addresses(
    rootAddress: str, 
    port: int):
    """Connect to a dns address and get the A records
    The IP address and port is at index [4][0]
    for example: ('13.250.46.106', 8333)

    Args:
        rootAddress (_type_): DNS address
        port (_type_): _description_

    Returns:
        _type_: list of peers in tuples (ip, port)
    """

    try:
        return [(info[4][0], info[4][1]) for info in socket.getaddrinfo(rootAddress, port,
                                                                    socket.AF_INET, socket.SOCK_STREAM,
                                                                    socket.IPPROTO_TCP)]
    except Exception as err:
        return []