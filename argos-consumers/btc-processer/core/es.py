from datetime import datetime
from elasticsearch import Elasticsearch

class ElasticsearchClient:
    def __init__(self, host, port, index, scheme="http"):
        self.index = index
        self.es = Elasticsearch([{'host': host, 'port': port, 'scheme': scheme}])

    def save_node_with_error(self, network, address, port, public_key, source, error, reason):
        self.save_node(network, address, port, public_key, source, {
            "error" : error,
            "reason" : reason
        })

    def save_node(self, network, address, port, public_key, source, metadata):
        document = {
            "network": network,
            "address": address,
            "port": port,
            "public_key": public_key,
            "source": source,
            "metadata": metadata,
            "updated": datetime.utcnow().isoformat()
        }

        node_id = f"{network}_{address}_{port}"

        if self.es.exists(index=self.index, id=node_id):
            self.es.update(index=self.index, id=node_id, body={"doc": document})
            print(f"Updated node {node_id}")
        else:
            document["created"] = document["updated"]
            self.es.index(index=self.index, id=node_id, body=document)
            print(f"Created new node {node_id}")
