# Operator Quickstart

This guide is for running ExTrace, not for changing its internals.

Use the root [README](../README.md) for the high-level project overview. Use
the agent docs under `documents/` only when you are modifying the system or
need exact historical state.

## Local Development Run

Prerequisites:

- Python 3.11+
- Docker / Docker Compose
- PostgreSQL 16 compatible runtime
- Node 20+ for UI work

From the repository root:

```bash
make install-dev
make up
make migrate
make dev
```

Open:

- UI: `http://127.0.0.1:3000`
- API docs: `http://127.0.0.1:8000/docs`
- noVNC executor view: `http://127.0.0.1:6080/vnc.html`

## Common Checks

```bash
make test-local
make test-security
make check-all
```

Targeted runs:

```bash
make ui-types-check
make ui-boundaries
make exec-up
make exec-run
make ui-up
make sim-target TARGET=publisher.name
make sim-all
make demo-canary
make demo-canary-offline
```

The smoke lane needs the smoke marker:

```bash
.venv/bin/pytest -m smoke
```

Other useful local commands:

```bash
cd ui && npm run dev
cd ui && npm run test
.venv/bin/pytest
.venv/bin/pytest -m "not smoke and not requires_db"
.venv/bin/pytest -m "requires_db"
```

## Analyzing An Extension

Typical options:

1. Use the UI marketplace flow.
2. Use the API to download and start an analysis.
3. Put an offline extension or VSIX under the expected local extension input
   path and run a target simulation.

Background analysis jobs are checked through:

```text
GET /api/marketplace/analyze/{job_id}
```

Do not treat "the command ran" as the same thing as verified behavior. Review
the activation report health, verification, and attempted-only fields.

## Air-Gapped Fedora Server

For an offline x86 Fedora Server, use the Podman bundle:

```bash
deploy/podman/build-bundle.sh
```

Copy the generated bundle to the server, then on the server:

```bash
mkdir -p ~/extrace && tar -C ~/extrace -xzf ~/extrace-podman-bundle.tgz
cd ~/extrace
sudo ./extrace-ctl.sh load
sudo ./extrace-ctl.sh up
sudo ./extrace-ctl.sh status
```

Full guide:

- [../deploy/podman/README.md](../deploy/podman/README.md)

## Remote Access

Default binding is loopback-only. For a headless server, prefer SSH tunnels:

```bash
ssh -L 3000:127.0.0.1:3000 -L 8000:127.0.0.1:8000 -L 6080:127.0.0.1:6080 user@fedora-host
```

Then open `http://localhost:3000` on your laptop.

Only bind services on a LAN after applying:

- [runbooks/lan-exposure.md](runbooks/lan-exposure.md)

## Where Outputs Go

By convention:

- Extension inputs live under `extensions/`.
- Reports land under `output/`.
- PostgreSQL stores catalog and analysis job metadata.

Generated or heavy trees such as `extensions/`, `output/`, `node_modules/`,
`ui/dist/`, `.venv/`, and caches should not be treated as source docs.
