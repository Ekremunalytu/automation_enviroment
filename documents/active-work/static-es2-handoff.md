# Static Analysis Pre-Check — ES-2 Session Handoff

`Status: ES-2 (hardened automation_static_analyzer container scaffold + runtime stub) is COMPLETE, FULLY VERIFIED (static + live), and COMMITTED + PUSHED to origin/static (user go-ahead 2026-05-30, after a rebuild + UI scan confirmed the stack healthy). Includes the 2026-05-30 doc-truth + Makefile reconciliation pass (see Verification).`

`Last Updated: 2026-05-30 — ES-2 implemented, verified, committed + pushed; doc-truth + Makefile pass folded in.`

`Branch: static · ES-2 committed on top of 67df007 (ES-1b); see git log on static for the hash.`

`Owner: ekrem`

This is a transient session-handoff (mirrors the `static-es1b-handoff.md`
pattern). The durable record is the stream tracker
[`static-analysis-pre-check-stream.md`](static-analysis-pre-check-stream.md)
(ES-2 already stamped DONE there) and [ADR 0016](../adrs/0016-static-analysis-pre-check-stage.md).

## Immediate next action

ES-2 is **done, committed, and pushed** to `origin/static` (user go-ahead
2026-05-30). The next iteration is **ES-3a** — the 6 in-house Python rules
(`s1`/`s2`/`s3`) + the real static runner that replaces the stub body behind the
frozen `static_runtime` invocation contract (see Open items below + the tracker
§ES-3a). The branch-contamination PR-strategy decision (see Open items) stays
OPEN and still gates any `static -> main` PR.

## Exact git state (at handoff)

- Branch `static`, HEAD `67df007` (= ES-1b, already pushed; `local == origin/static`).
- `static` is **10 commits ahead of `main`** (ES-0 `735fdf0`, ES-1a `33cfdfc`,
  ES-1b `67df007` + ~7 unrelated owner doc-truth/W22 commits). The
  branch-contamination PR-strategy decision is still OPEN (see Open items).
- ES-2 is entirely in the working tree (uncommitted): **8 modified + 7 new**.

Modified:

- `.env.example` · `Makefile` · `docker-compose.yml`
- `executor/binary_paths.py` · `executor/config.py`
- `tests/architecture/test_compose_isolation_invariants.py`
- `tests/executor/test_absolute_paths.py`
- `documents/active-work/static-analysis-pre-check-stream.md` (ES-2 stamp)

New (untracked):

- `static_runtime/` (`__init__.py`, `entrypoint.py`, `__main__.py`)
- `docker/static_analyzer/` (`Dockerfile`, `requirements.txt`, `Dockerfile.dockerignore`)
- `executor/static_host.py` · `executor/static_control.py`
- `tests/security/test_static_container_isolation.py`
- `tests/executor/test_static_control.py`
- `tests/smoke/test_static_container_smoke.py`

## What ES-2 did (summary; full detail in the tracker §ES-2)

Stands up the hardened `automation_static_analyzer` Docker boundary (ADR 0016
§Decision 2) + a producer-free runtime stub. Scaffold only — the container
writes an empty `StaticDetectionReport`. Feature flag stays OFF.

- `static_runtime/` — `python -m static_runtime` writes an empty
  `StaticDetectionReport` to `--report-path` (flags `--vsix-dir`,
  `--report-path`, `--rules-version`, `--timeout-budget-s`).
- `docker/static_analyzer/Dockerfile` — non-root `static`, copies only
  `packages/analysis_contracts` + `static_runtime` (NOT the dynamic engine).
- `docker-compose.yml` `static_analyzer` service — `network_mode: none`,
  `cap_drop: [ALL]`, no `cap_add`, `no-new-privileges`, 1g/1.0, ro extensions /
  rw results mounts, no docker.sock, no ports, idle via `sleep infinity`.
- `executor/static_host.py` + `static_control.py` — lean clones of
  `host.py` / `ExecutorControl`. Baked into the api image; DORMANT (no caller
  until ES-3b).
- `executor/config.py` — `StaticAnalyzerSettings` + `StaticAnalysisSettings`
  (`ENABLED` defaults False). `binary_paths.py` — `STATIC_ANALYZER_PYTHON3_PATH`.
- Makefile `static-build/build-nocache/up/down/shell/run-fixture` + isolation
  test enrolled in `test-security`. `.env.example` static block.

## Two deliberate deviations from the frozen handoff — DO NOT revert

1. **Runtime placement.** The frozen handoff put the runtime at
   `packages/analysis_engine/static_runtime/`. Rejected — `analysis_engine/__init__.py`
   eagerly imports `run_detection`, which would drag the whole dynamic engine
   into the minimal hardened image. The stub needs only
   `packages.analysis_contracts.static_detection` (pydantic-only; verified no
   back-edge to `analysis_engine`). → top-level `static_runtime/`; image copies
   `packages/analysis_contracts` + `static_runtime` only.
2. **Base image.** Used the api's already-audited
   `python:3.11-slim-bookworm@sha256:cd6733…` digest instead of the handoff's
   "3.12" (one audited base; guaranteed-pullable; 3.11 is fine for the
   pydantic-only stub).

## Verification — ALL GREEN (static + live)

Static (no container needed):

- `make check-all` → **2188 passed**, 9 skipped (lint/mypy/bandit/ui-types/
  ui-boundaries/markdownlint/test). +14 over ES-1b's 2174; no regressions.
- **Doc-truth + Makefile pass (2026-05-30):** added 3 container-free tests in
  `tests/executor/test_static_control.py` (stub on-disk JSON contract via
  `run_static_detection` + `main`, and the feature-flag default-OFF invariant);
  fixed a stale `3.12`→`3.11` base-image comment in `executor/binary_paths.py`;
  and reconciled the Makefile so the `static-*` targets + `up`/`rebuild`/`ps`
  output match the rest of the file (see next bullet). Re-ran the full gate:
  `make check-all` (postgres_test up) → **2191 passed**, 9 skipped — confirmed,
  no regressions (= 2188 + the 3 new tests).
- **Makefile consistency (2026-05-30):** `static-build` now mirrors
  `exec-build`/`ui-build` (clean 2-echo wrapper, plain `docker-compose build`;
  BuildKit-default honors the per-Dockerfile dockerignore allowlist) instead of
  the verbose BuildKit-progress dump; dropped `static-build-nocache` (no
  exec/ui analog — `make rebuild` is the no-cache path); added `static-down` to
  `help`; fixed the 1-char-overlong `static-run-fixture` help row. The ragged
  default `docker-compose ps` table (long image-digest column) that closed every
  `make up`/`rebuild` is replaced by a tidy `--format` table (shared
  `COMPOSE_PS_FORMAT` var across `up`/`rebuild`/`up-debug`/`ps`).

Live (after a Docker Desktop restart — see Gotchas):

- `make test-smoke` (ES-2) → **2 passed** (in-container import + stub writes a
  valid empty report).
- `make test-security` → **235 passed** (isolation test enrolled & green).
- `docker inspect automation_static_analyzer` → `NetworkMode=none`,
  `CapDrop=[ALL]`, `CapAdd=[]`, `SecurityOpt=[no-new-privileges:true]`,
  `Mem=1GiB`, `User=static` — runtime matches the compose-parse test exactly.
- Egress probe inside the container → `OSError` (network:none really blocks
  egress).
- Manual stub run produced a valid empty `StaticDetectionReport` JSON.

## Gotchas hit this iteration (carry forward)

- **Docker Desktop daemon wedged.** `docker build`/`ps`/`version` hung on
  `_ping` to `/Users/ekrem/.docker/run/docker.sock` (running containers stayed
  up, but the daemon API was unresponsive — likely after two long hung builds).
  Fix: fully quit + reopen Docker Desktop (`killall -9 Docker`; `pkill -9 -f
  com.docker`; `open -a Docker`), then `docker ps` returns fast. Build/smoke ran
  fine afterward. (Note: zsh does NOT treat inline `# comments` as comments —
  paste bare commands.)
- **Mac build-context slowness.** `docker/static_analyzer/Dockerfile.dockerignore`
  (allowlist) shrinks the static build context to a few files so Docker
  Desktop's slow macOS<->VM file sharing is a non-issue. Requires BuildKit
  (the `static-build` target sets `DOCKER_BUILDKIT=1`).
- **api bakes static_host.** `executor/static_host.py` + `static_control.py` are
  baked into the api image via `docker/api/Dockerfile` `COPY . .` (memory
  `project_api_bakes_host_orchestration`). DORMANT at ES-2; once ES-3b wires a
  caller, that needs `docker compose build api && up -d api`, not just executor.
- **No DB migration in ES-2** → the dev DB `extrace` gotcha
  (`project_dev_db_extrace_migration_gotcha`) does NOT apply this iteration.

## Open items / next iterations (NOT started)

- **ES-3a** — 6 in-house Python rules (`s1`/`s2`/`s3`) + the real static runner
  (mirrors `packages/analysis_engine/runner.py::run_detection`). Reuses the
  dynamic `a3_typosquat` matcher → the container's import surface gets revisited
  here (likely make `analysis_engine/__init__` lazy, or copy a narrower subtree).
- **ES-3b** — decision gate + orchestrator wiring. This is where the 7-step
  order (`static_analysis` + `decision_gate`) + `empty_job_steps` extension +
  `_TERMINAL_JOB_STATUSES += rejected_static` + `static_host`/`static_control`
  callers + `reject_analysis_job_static` land. Also: `/results` non-root write
  permission for the `static` uid (deferred from ES-2 — ES-2's smoke writes to
  `/tmp`, but ES-3b writes real reports to `/results`).
- **ES-4** — Semgrep (version-pinned wheel + 4 custom JS rules); rebuilds the
  static image (adds semgrep; pyyaml already pre-staged in requirements.txt).
- **ES-5** — close-out: UI surfaces, `AnalyzeResponse` extension, smoke evidence,
  feature-flag flip, ADR 0016 → Accepted.
- **Branch contamination (OPEN, user decision).** `static` is 10 commits over
  `main`; only 3 are static-stream (ES-0/1a/1b). Decide the PR strategy BEFORE
  any `static -> main` PR. Does not block further ES work on `static`.

## Read path for the next session

1. This handoff.
2. [`static-analysis-pre-check-stream.md`](static-analysis-pre-check-stream.md)
   (tracker; ES-2 §Per-Item Detail).
3. [ADR 0016](../adrs/0016-static-analysis-pre-check-stage.md) +
   [`extrace-static-stream-handoff.md`](extrace-static-stream-handoff.md)
   (frozen design intent; remember the two deviations above).
