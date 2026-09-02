
def parse_address(address):
    host, port = address.split(':')
    return host, int(port)