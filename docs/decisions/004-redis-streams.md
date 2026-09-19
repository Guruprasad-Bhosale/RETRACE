# ADR 004: Redis Streams for Worker Job Queues

## Status
Accepted

## Context
Long-running exploration and reproduction tasks must be queued and distributed to worker pools with acknowledgment and recovery guarantees.

## Decision
Use Redis Streams with consumer groups for job dispatching and analysis events.

## Rationale
* **Operational Simplicity:** Redis provides an in-memory datastore, caching layer, pub/sub, and persistent stream message queue in a single infrastructure dependency.
* **Consumer Groups:** Built-in message acknowledgments (XACK), pending entries lists (PEL), and consumer group claim mechanics prevent lost tasks.
* **Avoid Kafka Overkill:** Apache Kafka would introduce unnecessary operational overhead (Zookeeper/KRaft, partition tuning) without tangible benefits for this workload.

## Trade-offs
* Memory-bound persistence compared to disk-backed brokers like Kafka, mitigated by keeping job payloads lightweight and referencing object storage URIs.
