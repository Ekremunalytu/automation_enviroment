# apps/api

Week 1 skeleton for the future canonical API app surface.

This directory is intentionally documentation-only in Week 1. Runtime entry and
behavior still live in the current backend layout.

Planned role:

- host the canonical FastAPI app entrypoint after the refactor advances
- depend on shared packages rather than owning planner or contract internals
- stay thin at the request/response boundary
