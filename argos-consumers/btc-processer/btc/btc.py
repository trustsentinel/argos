import logging

from btc.protocol import connect_and_get_version

log: logging.Logger = logging.getLogger("btc")

async def process(es_client, peer_event):
    log.info(peer_event)

    metadata = await connect_and_get_version(host = peer_event['address'],port = peer_event['port'])

    if metadata.get("error") is not None:
        log.warning(f"skipping node due to error: {metadata['error']}, reason:  {metadata['reason']}")
        return

    version = metadata.get('version', 'unknown')

    log.info(f"saving node with address: {peer_event['address']} with protocol version: {version}")
    es_client.save_node(
        network=peer_event['network'],
        address=peer_event['address'],
        port=peer_event['port'],
        public_key=peer_event.get('public_key'),  # Use .get() to avoid KeyError if it's missing
        source=peer_event['source'],
        metadata={
            "version": version,  # Example dynamic metadata
            "network_type": metadata.get('network_type', 'unknown'),
            "network_utxo": metadata.get('network_utxo', False),
            "network_bloom": metadata.get('network_bloom', False),
            "network_witness": metadata.get('network_witness', False),
        }
    )

