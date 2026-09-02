import asyncio
import logging
from logging import Logger

from core import arguments
from processer import worker

log: Logger = logging.getLogger("main")
logging.getLogger("pika").setLevel(logging.WARNING)
logging.basicConfig(level=logging.INFO)

async def main():
    log.info(f"Initialisation of btc processor")
    await worker.process()

if __name__ == "__main__":
    asyncio.run(main())
