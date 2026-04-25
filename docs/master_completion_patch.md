# Master Completion Patch — Truthful Artifact Contract + DB Persistence + Storage Integrity

This patch makes artifact success truthful:

- StorageService is the authoritative local write path.
- Every stored artifact verifies non-zero size and SHA-256 checksum before becoming visible.
- Artifact contracts use `promotion_status=contract_verified` instead of pretending advanced gates have passed.
- Replayability, determinism, and drift budget are explicitly `pending`/`false` until real gates exist.
- TTS and batch workers persist generated artifact contracts into `audio_outputs` for durable lineage/debug.
- E2E verification accepts `contract_verified|promoted`, but still requires contract, lineage, write integrity, size, checksum, and reachable audio URL.

Advanced gates can later promote `contract_verified` artifacts to `promoted` only after replayability/determinism/drift checks pass.
