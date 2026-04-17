# packages/analysis_contracts

Week 1 skeleton for backend-owned analysis contracts.

No runtime models are moved here yet. Week 2 is expected to introduce the first
authoritative Pydantic v2 schemas for:

- activation report payloads
- trigger payloads
- related analysis job DTO surfaces when needed

Week 5 opens `packages/analysis_contracts/detection/` as the reserved
framework-agnostic surface for detection-owned contracts and helpers. Runtime,
storage, and UI code must continue to depend only on exported contracts, not on
rule implementations.
