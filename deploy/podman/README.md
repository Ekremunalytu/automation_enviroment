# ExTrace — Air-gapped Podman deployment (Fedora Server)

Run ExTrace on a **headless, air-gapped x86 Fedora Server** with **rootful
Podman** and **no extra dependencies** on the target (no compose, no internet).

The images are built once on an internet-connected machine, exported to a single
tarball, copied to the server, and run with plain `podman` via `extrace-ctl.sh`.

Related docs:

- [../../README.md](../../README.md) — project overview.
- [../../documents/operator-quickstart.md](../../documents/operator-quickstart.md) —
  local and deployment quickstart.
- [../../documents/how-it-works.md](../../documents/how-it-works.md) — readable
  system overview.

## Why this shape

The `api` container is an **orchestrator**: it mounts the container socket and
drives its siblings (`automation_executor`, `automation_static_analyzer`) via
`docker exec`. Podman exposes a **Docker-API-compatible socket**
(`/run/podman/podman.sock`), so the baked-in Docker CLI in the api image works
unchanged once that socket is mounted at `/var/run/docker.sock`. No application
code changes are needed — only correct wiring (this directory).

## Topology

| Machine | Role | Needs internet |
|---|---|---|
| Build box (your Mac, or the ASUS TUF) | builds + exports images | **yes** |
| Fedora Server (x86, headless) | runs ExTrace | no (air-gapped) |

> **Arch note:** the target is **amd64**. Building on the Apple Silicon Mac
> cross-builds `linux/amd64` under QEMU — works, but the **executor image is
> slow** (VS Code + Chromium + Node under emulation). Building on the **x86 ASUS
> TUF** (native amd64) is much faster and risk-free. `build-bundle.sh` handles
> both automatically.

---

## 1. On the build box (internet + docker)

```bash
# from the repo root
deploy/podman/build-bundle.sh
# → deploy/podman/dist/extrace-podman-bundle.tgz
```

This builds `api`, `executor`, `static-analyzer`, `ui`, pulls `postgres`,
`docker save`s them into `images.tar.gz`, and bundles the controller + env
template into one `.tgz`.

> To build on the ASUS TUF instead: copy the repo there, install Docker (or
> Podman: `ENGINE=podman deploy/podman/build-bundle.sh`), run the same command.

## 2. Transfer to the Fedora Server

```bash
scp deploy/podman/dist/extrace-podman-bundle.tgz user@fedora-host:~/
# or via USB if fully air-gapped
```

## 3. On the Fedora Server (rootful)

```bash
mkdir -p ~/extrace && tar -C ~/extrace -xzf ~/extrace-podman-bundle.tgz
cd ~/extrace

# (optional) review/edit secrets & ports — dev defaults work for a test box
nano extrace.env        # rotate POSTGRES_PASSWORD if exposing beyond loopback

sudo ./extrace-ctl.sh load     # load images + enable rootful podman.socket (once)
sudo ./extrace-ctl.sh up       # start everything
sudo ./extrace-ctl.sh status
```

Services (loopback by default — ADR 0007):

- UI       → `http://127.0.0.1:3000`
- API docs → `http://127.0.0.1:8000/docs`
- noVNC    → `http://127.0.0.1:6080` (watch the executor desktop)

## 4. Run malware tests

Drop extension folders or `.vsix` files into `~/extrace/extensions`
(air-gapped offline VSIX → `~/extrace/extensions/offline`). Reports land in
`~/extrace/output`. Drive a scan from the API, the UI, or directly:

```bash
sudo ./extrace-ctl.sh exec executor \
  python3 -m executor.flows.playwright.entrypoint --monitor --target-extension-id publisher.name
```

## Controller cheatsheet

```bash
sudo ./extrace-ctl.sh logs executor    # follow logs (api|executor|static|ui|db)
sudo ./extrace-ctl.sh exec api bash    # shell into a container
sudo ./extrace-ctl.sh down             # stop (keeps DB volume)
sudo ./extrace-ctl.sh restart
sudo ./extrace-ctl.sh destroy          # wipe containers + DB volume
```

---

## Accessing the headless server from your laptop

Default binding is **loopback only**. Prefer an SSH tunnel over LAN exposure:

```bash
ssh -L 3000:127.0.0.1:3000 -L 8000:127.0.0.1:8000 -L 6080:127.0.0.1:6080 user@fedora-host
# then browse http://localhost:3000 on your laptop
```

To bind on the LAN instead (firewall it, rotate `POSTGRES_PASSWORD` first):

```bash
sudo EXTRACE_BIND=0.0.0.0 ./extrace-ctl.sh up
```

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `api` logs: `cannot connect to docker daemon` | rootful podman socket not up → `sudo systemctl enable --now podman.socket`; confirm `/run/podman/podman.sock` exists. |
| `api` can't `docker exec` the executor | run everything **rootful** (`sudo`) so api's socket and the containers live in the same podman. Don't mix rootless. |
| `permission denied` on `extensions`/`output` | SELinux relabel — the controller mounts these with `:z`. If you moved dirs, re-run `up`. |
| Postgres healthy but api exits | migrations need the DB; the controller waits for `pg_isready` before starting api. Check `logs db`. |
| executor `Target crashed` / inconclusive | `/dev/shm` too small for heavy targets → raise `EXECUTOR_SHM_SIZE=2g` in `extrace.env`, then `restart`. |
| Build fails on Apple Silicon | QEMU/amd64 emulation flake → build on the x86 ASUS TUF (native), or retry the failing image. |

## What this does NOT do

- Rootless Podman (chosen mode is rootful — simplest for socket orchestration).
- `postgres_test` / `executor-cdp` (dev/CI/debug only — intentionally omitted).
- Auto-update; rebuild the bundle and re-`load` to ship new images.
