# ADR 0013 — Container Isolation Baseline

- Status: Accepted (`2026-05-28`)
- Date: 2026-05-28
- Authors: ekrem + Claude
- Driving phase: W21-4 — `[GOAL container-hardening-baseline]` —
  STRETCH pulled into W21 per user direction `2026-05-28` after W21-1
  + W21-2 closed cleanly

## Context

The PoC's threat model (`documents/adrs/0002-threat-model.md`) lists
A1–A7 adversary classes that we treat as in-scope. The marketplace
analyzer runs untrusted VS Code extension code inside the
`automation_executor` container (executor's Dockerfile installs
xvfb + VS Code + Playwright + Node + Python on a debian base). Prior
to W21-4 the only container-level hardening on that runtime is:

- `automation_executor`: explicit `cap_add: [NET_RAW, SYS_PTRACE]`
  (required by `tcpdump`/`tshark`/`strace` for malware-detection
  observability per executor/container/Dockerfile L30-L33), plus
  `mem_limit` + `cpus` from W14 close-out.
- `automation_api`, `automation_ui`: no explicit security directives.
- `postgres` / `postgres_test`: image digest pinned (W15-7), no caps
  added. Named volume only.

That posture is weaker than the threat model's intent. A misbehaving
extension can request any capability Docker's default keepset
grants (CAP_CHOWN, CAP_DAC_OVERRIDE, CAP_FOWNER, CAP_KILL, CAP_SETUID,
CAP_SETGID, …), and a privilege-escalation surface (set-uid binaries)
remains exploitable. The W21-4 audit closes the easy half of that gap:
**drop every capability we don't actually need, and refuse new
privileges.**

The second half — read-only root filesystem + custom seccomp profile +
tmpfs mounts — is **explicitly deferred** to W22 because it requires
restructuring write surfaces (`/home/executor/.vscode-server`,
`/run/extrace` for W13-1 secrets, stimulus materialization paths under
`/tmp`) that need their own iteration to validate via live-run smoke
on `ms-python.python`. The baseline lands first; the ratchet-down
follows when the fixture restructuring is in scope.

## Decision

For each runtime service in `docker-compose.yml`:

| Service | `cap_drop` | `cap_add` (kept) | `security_opt` | `read_only` | `tmpfs` |
|---|---|---|---|---|---|
| `automation_executor` | `[ALL]` | `[NET_RAW, SYS_PTRACE, SETUID, SETGID, SETPCAP]` | `["no-new-privileges:true"]` | **deferred to W22** | **deferred to W22** |
| `automation_api` | `[ALL]` | `[SETUID, SETGID]` | `["no-new-privileges:true"]` | **deferred to W22** | **deferred to W22** |
| `automation_ui` | `[ALL]` | `[SETUID, SETGID, CHOWN, DAC_OVERRIDE]` | `["no-new-privileges:true"]` | **deferred to W22** | **deferred to W22** |
| `postgres` / `postgres_test` | unchanged | unchanged | unchanged | unchanged (named volume needs write) | unchanged |
| `executor-cdp` (debug profile) | unchanged | unchanged | unchanged | unchanged (opt-in debug; not part of the default attack surface) | unchanged |

### SETUID + SETGID retention for `api` and `ui`

Live-run smoke during the W21-4 primary commit surfaced that both
`automation_api` and `automation_ui` use a `gosu`-style entrypoint
that drops from root to an unprivileged user (`appuser` for api,
`nginx` for ui) before launching the workload. That user-switching
requires CAP_SETUID + CAP_SETGID at runtime; with `cap_drop: [ALL]`
both are removed and the entrypoint exits with `error: failed
switching to "appuser": operation not permitted`.

The retention is intentional and bounded:

- The caps are used **once at startup** for the privilege drop, then
  the long-running process runs as the unprivileged user.
- `no-new-privileges:true` still prevents any further setuid binary
  exec from gaining new privileges — it only allows the privilege
  *drop* the entrypoint needs.
- Future ratchet-down option (W22+): restructure the api/ui
  Dockerfiles to use a static `USER` directive (like the executor
  Dockerfile does at line 153) so the runtime never needs setuid
  syscalls and these caps can be dropped too.

### UI nginx caps (extension of SETUID + SETGID retention)

The `automation_ui` service runs the official nginx Docker image,
whose entrypoint does more than a simple privilege drop:

1. `chown(/var/cache/nginx/client_temp, 101)` — sets the cache dir
   to the unprivileged `nginx` user before workers fork.
2. Drop to user 101 via setuid/setgid for the worker processes.

The chown step needs CAP_CHOWN; the worker drop needs SETUID +
SETGID; defensive include CAP_DAC_OVERRIDE so the master can still
read configuration files after the chown. CAP_NET_BIND_SERVICE is
NOT required because the listener (port 3000) is non-privileged.

Surfaced during the W21-4 primary live-run smoke (api came up
healthy after adding SETUID+SETGID, ui still failed with
`chown(...) failed: Operation not permitted` until CHOWN +
DAC_OVERRIDE were added). The ratchet-down option (static USER
directive in `ui/Dockerfile` + pre-chowned cache dir) is W22+.

### Network capture under no-new-privileges (`2026-05-29` follow-up)

The W21-4 baseline shipped `cap_add: [NET_RAW, SYS_PTRACE]` on the
executor specifically so `tshark`/`tcpdump` could capture packets. A
post-merge investigation on `2026-05-29` found that **network capture
had silently stopped working** ever since the baseline landed —
`activation_report` files showed `network_events: 0` and
`network_capture_error: "tshark: ... You don't have permission to
capture on that device"`, whereas pre-baseline reports captured 150+
events.

Root cause: the executor runs the workload as the unprivileged
`executor` user (Dockerfile `USER executor`), and `dumpcap` obtains
CAP_NET_RAW via a **file capability** (`setcap cap_net_raw+eip`,
Dockerfile L93-94). `no-new-privileges:true` (`PR_SET_NO_NEW_PRIVS`)
**disables file-capability elevation at `execve`** — so dumpcap's file
cap is nullified, and a non-root `docker exec` process gets no effective
caps from `cap_add` either (cap_add only seeds the bounding set for
non-root). Net result: tshark runs with an empty effective set and
cannot open a raw socket. (The original §Operational-notes smoke
expectation that `CapEff` would show NET_RAW for the executor was
therefore incorrect — a non-root process's `CapEff` is `0`.)

Decision: keep `no-new-privileges:true` and grant CAP_NET_RAW as an
**ambient** capability instead of relying on the file cap. Ambient caps
survive both a uid transition and `execve` under no_new_privs, so they
reach the docker-exec'd monitor process tree (`python` → `tshark`).
Mechanics:

- `executor.host.run_playwright_automation` runs the monitor exec as
  root (`docker exec -u 0 ...`) and prepends
  `/usr/local/bin/monitor_entrypoint.sh` to the command.
- `monitor_entrypoint.sh` (root) calls `setpriv --reuid=executor
  --regid=executor --init-groups --inh-caps=+net_raw
  --ambient-caps=+net_raw -- python3 -m ...entrypoint --monitor ...`.
  The workload therefore runs as the **executor** user (same uid as VS
  Code — the same-UID model is preserved) with CAP_NET_RAW effective.
  Only `setpriv` runs in the brief root window; the monitor workload is
  never root.
- If the ambient grant is unavailable (e.g. a stale container without
  the new caps), the wrapper probes first and falls back to a plain user
  drop, so the rest of the monitor (file/process/strace capture) still
  runs and only network capture is lost. It never runs the workload as
  root.

This requires three more caps on the executor, used **once per monitor
exec** by setpriv and bounded exactly like the api/ui SETUID+SETGID
retention above:

- **SETUID + SETGID** — to drop root → executor.
- **SETPCAP** — to raise NET_RAW into the inheritable+ambient sets.

These are not in-container escalation vectors: the workload runs as the
unprivileged executor user under `no-new-privileges:true`, so code
inside the container cannot regain them (no file caps, no setuid, no
ambient beyond NET_RAW). The wrapper is exec'd as root and is therefore
shipped root-owned + non-writable by the executor UID (Dockerfile +
`tests/architecture/test_executor_runtime_script_permissions.py`), the
same ratchet that protects `launch_vscode.sh`.

Future ratchet-down option (W22+): a dedicated capture sidecar sharing
the executor's network namespace would let the executor drop NET_RAW +
the setpriv trio entirely, at the cost of a new service and out-of-process
capture plumbing.

### Rationale

1. **`cap_drop: [ALL]`** is the strongest single change a compose
   file can make. Docker's default keepset is permissive
   (CAP_AUDIT_WRITE, CAP_CHOWN, CAP_DAC_OVERRIDE, CAP_FOWNER,
   CAP_FSETID, CAP_KILL, CAP_MKNOD, CAP_NET_BIND_SERVICE,
   CAP_NET_RAW, CAP_SETFCAP, CAP_SETGID, CAP_SETPCAP, CAP_SETUID,
   CAP_SYS_CHROOT) — every one of those is reachable by code inside
   the container and several (CAP_SETUID, CAP_SETGID, CAP_DAC_OVERRIDE,
   CAP_CHOWN, CAP_MKNOD) trivially enable privilege escalation if a
   set-uid binary is present. Dropping all + adding back only the
   audited monitoring + privilege-drop capabilities (`NET_RAW`,
   `SYS_PTRACE`, `SETUID`, `SETGID`, `SETPCAP`) on the executor
   eliminates the bulk of the cap-based escalation paths (see
   §Network capture under no-new-privileges for why the setpriv trio
   `SETUID`/`SETGID`/`SETPCAP` is retained).

2. **`security_opt: ["no-new-privileges:true"]`** prevents any
   process inside the container from gaining new privileges via
   set-uid binaries. This is a cheap, well-tested kernel flag
   (`PR_SET_NO_NEW_PRIVS`) that has no impact on legitimate Node
   /Python/uvicorn workloads. It is the natural pair for `cap_drop:
   [ALL]` because it closes the residual set-uid path.

3. **`postgres` / `postgres_test` stay as-is** because the postgres
   image's healthcheck + initial schema setup needs CAP_CHOWN to
   chown the data directory at first run. The image is digest-pinned
   (W15-7) so the supply-chain risk is bounded. Adding `cap_drop:
   [ALL]` here would require an upstream Dockerfile change or a
   custom entrypoint, which is W22+ scope.

4. **`executor-cdp` is opt-in (debug profile)** and only runs when an
   operator explicitly invokes `make up-debug`. It is not part of the
   default attack surface that an unauthenticated marketplace analyze
   would expose, so baseline hardening targets the always-on services
   first.

### Deferred to W22+ (documented for the ratchet-down lane)

- **`read_only: true` + `tmpfs` mounts** — requires identifying every
  write path inside the container and either bind-mounting a writable
  volume or providing a tmpfs. For `automation_executor` the known
  write paths are:
  - `/workspace` — already a bind mount with `executor` user
    ownership (executor/container/Dockerfile L101-L102). Writable.
  - `/results` — bind mount; writable.
  - `/extensions-input` — bind mount `:ro`; already read-only.
  - `/home/executor/.vscode` — created by the Dockerfile at L115-L116;
    VS Code Extension Host adds `.vscode-server`, `.config/Code`, and
    auxiliary cache dirs at activate() time. Would need a tmpfs mount
    sized to hold those caches.
  - `/run/extrace` — W13-1 HMAC secret distribution path. Would need
    a tmpfs mount or stay writable.
  - `/tmp` — stimulus materialization (per
    `executor/flows/playwright/stimulus/materializers.py`). Would
    need a tmpfs.

  Each of these needs measured (size, retention, cross-restart
  semantics) before flipping to `read_only: true`. W22 lane.

- **Custom `seccomp` profile** (`docker/seccomp.json`) — Docker's
  default seccomp profile is already active when no `security_opt`
  is set for seccomp. The default profile blocks ~50 dangerous
  syscalls (e.g., `kexec_load`, `bpf`, `clone3` with specific flags,
  `ptrace` from non-CAP_SYS_PTRACE processes) which is a meaningful
  hardening already. A custom profile that ratchets down further
  (e.g., blocking `unshare`, restricting `mount`, denying
  `personality` calls that switch ABI) requires an audit pass to
  confirm Playwright + Xvfb + VS Code don't depend on any of them.
  W22 ratchet-down lane.

## Consequences

### Positive

- Drops the majority of cap-based privilege escalation paths
  inside `automation_executor` (the highest-risk service that runs
  untrusted extension code).
- `no-new-privileges:true` closes the residual set-uid path even if
  a set-uid binary remains in the executor image.
- Establishes a baseline that future iters can ratchet down from
  (`read_only`, custom seccomp) without revisiting the cap audit.
- Adds a `tests/architecture/` invariant test (`test_compose_isolation_invariants.py`)
  that pins the cap_drop + no-new-privileges shape so future
  compose edits cannot silently regress.

### Negative

- The deferred items (read_only + custom seccomp + tmpfs) leave a
  measurable gap between the W21-4 baseline and the eventual
  target. ADR documents the gap so it cannot be lost.
- `postgres` / `postgres_test` keep their default cap keepset.
  Lower priority because they don't run untrusted code and they're
  digest-pinned.

### Operational notes (manual smoke checklist)

Before merging the W21 close-out PR, an operator MUST verify the
hardened compose still permits the standard analyze flow:

```bash
# 1. Bring the stack up with the hardened compose.
make exec-up

# 2. Verify cap_drop + no-new-privileges took effect on the executor.
docker exec automation_executor cat /proc/self/status | grep -E "Cap|NoNewPrivs"
# Expected: NoNewPrivs:	1
# Expected: CapEff:	0000000000000000  (the executor process runs non-root,
#   so it holds NO effective caps — cap_add only seeds the BOUNDING set,
#   CapBnd. Expect CapBnd to contain SETGID (bit 6) + SETUID (bit 7) +
#   SETPCAP (bit 8) + NET_RAW (bit 13) + SYS_PTRACE (bit 19) =
#   0x00000000000821c0.)
# 2b. Verify network capture actually gets NET_RAW effective via the
#     ambient-cap drop wrapper (the real signal — see §Network capture
#     under no-new-privileges):
docker exec -u 0 automation_executor /usr/local/bin/monitor_entrypoint.sh \
  grep CapEff /proc/self/status
# Expected: CapEff:	0000000000002000  (NET_RAW = bit 13, set as ambient and
#   preserved across the setpriv drop to the executor user).

# 3. Trigger an analyze for ms-python.python.
curl -X POST http://127.0.0.1:8000/api/marketplace/analyze/start \
  -H 'Content-Type: application/json' \
  -d '{"publisher":"ms-python","name":"python","version":"2026.5.2026052501"}'

# 4. Poll until status=completed; expected ~3-5 minutes.
# 5. Verify the new activation_report shows no regression in
#    coverage_summary vs the prior W21-2 anchor 1ddb3702c0ca
#    (missing_capabilities = [chat]; W19 invariants hold).
```

If the smoke fails on cap-related symptoms (e.g., `chown: operation
not permitted` in container startup), the audit may need to keep
CAP_CHOWN on the affected service. Document the addition and the
rationale in this ADR before re-running.

## Status / next steps

- W21-4 primary commit lands this ADR + the docker-compose.yml diff
  + `tests/architecture/test_compose_isolation_invariants.py`.
- W21-4 self-stamp commit records the live-run smoke anchor.
- W22+ ratchet-down lane: `read_only: true` + tmpfs mounts +
  custom `docker/seccomp.json` profile.

## References

- `documents/adrs/0002-threat-model.md` — A1–A7 adversary classes.
- `documents/adrs/0007-local-network-binding.md` — loopback-only
  default for host ports.
- `documents/adrs/0008-container-packaging.md` — Dockerfile pattern
  + digest pinning.
- `documents/adrs/0011-unauthenticated-catalog-endpoints-posture.md`
  — Option A acceptance.
- Docker default seccomp profile — `moby/moby` repository under
  `profiles/seccomp/default.json` (canonical source for the
  ~50-syscall blocklist Docker applies by default).
- Linux capabilities reference — `man 7 capabilities`.
