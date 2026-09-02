import asyncio
import logging

from logging import Logger
import traceback

from core import arguments
from core.arguments import int_range
from network import worker

log: Logger = logging.getLogger("main")
logging.basicConfig(level=logging.INFO)
logging.getLogger("pika").setLevel(logging.WARNING)

async def main(network_type, max_peers, max_depth):
    try:
        log.info(f"Initialisation with network={network_type}, max_peers={max_peers}")
        await worker.process(network_type, max_peers, max_depth)
    except Exception as e:
        log.error(f"An error occurred: {str(e)}")
        log.error(traceback.format_exc())
    finally:
        await worker.close()

if __name__ == "__main__":
    flags = [
        {
            "name": "--network",
            "choices": ["btc", "eth"],
            "help": "Specify the network (btc or eth).",
            "required": True
        },
        {
            "name": "--maxpeers",
            "type": int_range,
            "help": "Specify the maximum number of peers (0-100, -1 allowed), default is 20",
            "default": 10,
            "required": False
        },
        {
            "name": "--maxdepth",
            "type": int_range,
            "help": "Specify the maximum number of peers (0-15, -1 allowed), default is 5",
            "default": 5,
            "required": False
        }
    ]
    args = arguments.setup(flags, "Run the script on a specific network")
    asyncio.run(main(args.network, args.maxpeers, args.maxdepth))
