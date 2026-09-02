# Reference: Kuipeers network-discovery modules

Predecessor peer-discovery code lifted from the **Kuipeers** project (2024) —
the direct ancestor of argos — as reference to fold into argos's consumer
pipeline.

Worth integrating:
- `kuinetworks/bitcoin/discovery.py` — Bitcoin gossip-based peer discovery
- `kuinetworks/peers.py`, `net.py`, `modules.py` — peer model + per-network module system
- `kuicore/` — shared argument-parsing / net helpers

Reference only (not wired into argos). Integration & modernization (asyncio,
pydantic) happen in Phase 5. gitleaks: clean.
