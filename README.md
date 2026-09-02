# argos

Distributed P2P blockchain network scanning & vulnerability-analysis pipeline.

`Status: Active` · `Python · AMQP · Elasticsearch` · part of [TrustSentinel](https://trustsentinel.eu)

## Overview
argos continuously discovers and monitors nodes on decentralized networks
(Bitcoin, Ethereum). AMQP consumers and per-network processors find peers,
classify them by ASN / ISP / geolocation, scan for known vulnerabilities, and
stream findings to Elasticsearch.

## Layout
- `argos-consumers/` — AMQP workers + per-network processors (btc, eth)
- `argos-explorer/` — node discovery
- `reference/kuinetworks/` — predecessor discovery code (Kuipeers) to integrate

## License
MIT

<sub>Successor to bluebycode/argos-explorer and the Kui family; continued under TrustSentinel.</sub>
