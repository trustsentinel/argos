
BOOT_NODES = [
"enode://d2b720352e8216c9efc470091aa91ddafc53e222b32780f505c817ceef69e01d5b0b0797b69db254c586f493872352f5a022b4d8479a00fc92ec55f9ad46a27e@88.99.70.182:30303"
]

def get_bootnodes():
    return BOOT_NODES

async def get_neighbours(bootnode):
    return [(bootnode, 0, None)]