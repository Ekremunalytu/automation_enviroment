#!/bin/bash
# =============================================================================
# ExTrace monitor entrypoint — privilege-drop wrapper for the analyze monitor.
#
# Host-side `executor.host.run_playwright_automation` invokes the in-container
# monitor via:
#   docker exec -u 0 ... automation_executor \
#       /usr/local/bin/monitor_entrypoint.sh \
#       /usr/bin/python3 -m executor.flows.playwright.entrypoint --monitor ...
#
# The monitor runs raw packet capture (tshark/dumpcap — see
# executor/flows/playwright/runtime_capture/network.py) which needs
# CAP_NET_RAW in its *effective* set.
#
# ADR 0013 sets `security_opt: no-new-privileges:true`. That flag nullifies
# dumpcap's `cap_net_raw+eip` file capability (no_new_privs disables file-cap
# elevation at execve), and a non-root `docker exec` process gets no effective
# caps from `cap_add` either. So instead of relying on the file capability we
# grant CAP_NET_RAW as an *ambient* capability: start the exec as root, raise
# NET_RAW into the inheritable+ambient sets, and drop to the unprivileged
# `executor` user via setpriv. Ambient caps survive BOTH the uid transition
# and the execve into python under no_new_privs, so the whole monitor process
# tree (python -> tshark) runs as `executor` with CAP_NET_RAW effective — the
# same uid as VS Code, preserving the same-UID threat model. The monitor
# workload itself is NEVER run as root; only setpriv runs in the brief root
# window before the drop.
#
# Graceful degradation: if the ambient grant is unavailable (e.g. a stale
# container provisioned before the SETUID/SETGID/SETPCAP cap_add landed),
# fall back to a plain user drop so the rest of the monitor (file / process /
# strace capture) still runs — only network capture is lost, matching the
# pre-fix behavior. The probe ensures we never lose the whole monitor run to a
# setpriv error.
#
# Tamper-proofing: this script is exec'd as ROOT, so a writable copy would be
# an executor->root escalation. It ships root:root and is NOT writable by the
# executor UID (Dockerfile chmod 0755 + no executor chown;
# tests/architecture/test_executor_runtime_script_permissions.py pins it).
# =============================================================================
set -u

SETPRIV=/usr/bin/setpriv
TARGET_USER=executor
DROP_ARGS=(--reuid="${TARGET_USER}" --regid="${TARGET_USER}" --init-groups)
CAP_ARGS=(--inh-caps=+net_raw --ambient-caps=+net_raw)

if [ "$#" -eq 0 ]; then
    echo "[monitor-entry] ERROR: no command given to execute" >&2
    exit 2
fi

# Already unprivileged (wrapper invoked without `-u 0`): run as-is. Network
# capture only works if the caller already holds CAP_NET_RAW; the rest of the
# monitor is unaffected.
if [ "$(id -u)" != "0" ]; then
    exec "$@"
fi

# Probe whether the ambient CAP_NET_RAW grant succeeds in this container before
# committing the real exec. If the caps were not provisioned (stale container),
# setpriv errors and we must NOT lose the whole monitor run.
if "${SETPRIV}" "${DROP_ARGS[@]}" "${CAP_ARGS[@]}" -- /bin/true 2>/dev/null; then
    exec "${SETPRIV}" "${DROP_ARGS[@]}" "${CAP_ARGS[@]}" -- "$@"
fi

echo "[monitor-entry] WARN: CAP_NET_RAW ambient grant unavailable; network" \
    "capture disabled (other monitors unaffected). Verify executor cap_add" \
    "includes SETUID/SETGID/SETPCAP/NET_RAW (ADR 0013)." >&2
exec "${SETPRIV}" "${DROP_ARGS[@]}" -- "$@"
