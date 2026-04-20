# apps/api

`Last Updated: 2026-04-20`

This directory is a historical placeholder, not the canonical API runtime
surface.

Current reality:

- FastAPI entry and behavior live in `main.py`
- workflow orchestration lives in `workflows/`
- shared platform code lives in `appcore/`
- framework-agnostic contracts and planner logic live in `packages/`

Do not treat `apps/api/` as an active migration target unless a new plan or ADR
promotes it explicitly.
