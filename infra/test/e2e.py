"""End-to-end test of the argos pipeline.

Publishes a synthetic btc peer event (pointing at the mock-btc node) to the
broker, then asserts the btc-processer consumed it, probed the node, and indexed
the finding in Elasticsearch. This exercises the whole chain that the explorer
would drive in production, without depending on the live network.

We (re)publish on every poll: a fanout message is only delivered to queues that
are already bound, so republishing absorbs the consumer's start-up race. The
event is idempotent (same node id), so repeats are harmless.
"""
import json
import os
import sys
import time

import pika
from elasticsearch import Elasticsearch

AMQP_HOST = os.getenv("AMQP_HOST", "rabbitmq")
AMQP_USER = os.getenv("AMQP_USER", "user")
AMQP_PASS = os.getenv("AMQP_PASS", "password")
EXCHANGE = os.getenv("AMQP_EXCHANGE", "peers-discovered")
ES_URL = os.getenv("ES_URL", "http://elasticsearch:9200")
INDEX = os.getenv("ES_INDEX", "peers")
TIMEOUT_S = int(os.getenv("E2E_TIMEOUT", "120"))

PEER = {
    "network": "btc",
    "address": os.getenv("MOCK_BTC_HOST", "mock-btc"),
    "port": 8333,
    "public_key": None,
    "source": "e2e",
}
NODE_ID = f'{PEER["network"]}_{PEER["address"]}_{PEER["port"]}'


def publish_once() -> None:
    params = pika.ConnectionParameters(
        host=AMQP_HOST,
        credentials=pika.PlainCredentials(AMQP_USER, AMQP_PASS),
    )
    conn = pika.BlockingConnection(params)
    try:
        ch = conn.channel()
        ch.exchange_declare(exchange=EXCHANGE, exchange_type="fanout")
        ch.basic_publish(exchange=EXCHANGE, routing_key="", body=json.dumps(PEER))
    finally:
        conn.close()


def main() -> int:
    es = Elasticsearch(ES_URL)
    deadline = time.time() + TIMEOUT_S
    published = 0
    while time.time() < deadline:
        try:
            publish_once()
            published += 1
        except Exception as exc:  # broker not accepting connections yet
            print(f"e2e: broker not ready ({exc!r}); retrying", flush=True)
            time.sleep(2)
            continue
        try:
            if es.exists(index=INDEX, id=NODE_ID):
                doc = es.get(index=INDEX, id=NODE_ID)["_source"]
                print(
                    f"ARGOS E2E RESULT: PASS  "
                    f"(event published -> consumed -> probed mock-btc -> indexed {NODE_ID})",
                    flush=True,
                )
                print(json.dumps(doc, indent=2), flush=True)
                return 0
        except Exception as exc:  # ES not ready yet
            print(f"e2e: elasticsearch not ready ({exc!r}); retrying", flush=True)
        time.sleep(2)

    print(
        f"ARGOS E2E RESULT: FAIL  (doc {NODE_ID} not found after {published} publishes "
        f"in {TIMEOUT_S}s)",
        flush=True,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
