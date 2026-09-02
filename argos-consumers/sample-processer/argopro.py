import asyncio
import logging
from logging import Logger

from core import arguments
from processer import worker

log: Logger = logging.getLogger("main")
logging.getLogger("pika").setLevel(logging.WARNING)
logging.basicConfig(level=logging.INFO)

async def main(network_type):
    log.info(f"Initialisation peers processors for network={network_type}")
    await worker.process(network_type)

if __name__ == "__main__":
    flags = [
        {
            "name": "--network",
            "choices": ["btc", "eth"],
            "help": "Specify the network (btc or eth).",
            "required": True
        }]
    args = arguments.setup(flags, "Run the script on a specific network")
    asyncio.run(main(args.network))
