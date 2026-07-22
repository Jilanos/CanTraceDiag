# Storage Decision - PWA Local Engine 0.2

Status: incremental decision for milestone 0.2.

## Decision

Use a columnar in-browser store for this milestone, backed by arrays of primitive
columns rather than retained per-frame objects. The store ingests frames/events
by batch and exposes query methods matching the current API concepts.

Persistence is intentionally not final in 0.2:

- IndexedDB is the likely next step for workspace metadata and small persisted
  manifests.
- OPFS remains the candidate for large local index artifacts and copied trace
  data.
- DuckDB-WASM is deferred until query benchmarks prove that its packaging and
  worker complexity are justified.

## Rationale

The 0.1 spike proved chunked browser scanning. The next unknown is semantic
parity and query shape, not durable storage. A columnar store keeps the memory
model closer to the desired large-file path while allowing fast fixture parity
tests without locking the project into a storage engine too early.

## Follow-Up Before 0.3

- Benchmark IndexedDB batch writes and reads on 50/150/500 MiB synthetic traces.
- Benchmark OPFS file-backed indexes for trace rows and selected signal caches.
- Reconsider DuckDB-WASM only after query benchmarks show clear value.
