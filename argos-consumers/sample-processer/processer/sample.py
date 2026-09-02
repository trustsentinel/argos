import logging
log: logging.Logger = logging.getLogger("sample")

def process(peer_event):
    log.info(peer_event)
