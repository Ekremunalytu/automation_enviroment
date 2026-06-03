#!/bin/bash
# =============================================================================
# ExTrace Executor Startup
# Starts Xvfb + Openbox + x11vnc + noVNC + VS Code, then keeps alive
# =============================================================================

set -euo pipefail

DISPLAY_VALUE="${EXECUTOR_DISPLAY:-${DISPLAY:-:99}}"
SCREEN_VALUE="${EXECUTOR_SCREEN:-1920x1080x24}"
VNC_HOST_VALUE="${EXECUTOR_VNC_HOST:-localhost}"
VNC_PORT_VALUE="${EXECUTOR_VNC_PORT:-5900}"
NOVNC_PORT_VALUE="${EXECUTOR_NOVNC_PORT:-6080}"
# W14-3 (M14b): CDP is opt-in; an empty default keeps the unauthenticated
# debug port closed in routine `make up` boots. Operators who need CDP
# (e.g. `make up-debug`) set EXECUTOR_CDP_PORT explicitly in the
# environment before container start.
CDP_PORT="${EXECUTOR_CDP_PORT:-}"
STARTUP_SLEEP_SECONDS="${EXECUTOR_STARTUP_SLEEP_SECONDS:-1}"
PLAYWRIGHT_FLOW_DIR="${EXECUTOR_PLAYWRIGHT_FLOW_DIR:-/home/executor/flows/playwright}"
HARNESS_SHA256_MANIFEST="${EXECUTOR_HARNESS_SHA256_MANIFEST:-/home/executor/flows/harness_extension.sha256}"

# W8-0: deterministic epoch identifier for the harness ready-marker
# handshake. Generated once per container boot and inherited by every
# spawned process (notably VS Code → extension host → harness
# extension). Python-side `_ensure_harness_ready_with_recovery` reads
# the same env var and rejects markers whose `epoch_run_id` does not
# match (stale from a previous container life).
EXTRACE_EPOCH_RUN_ID="${EXTRACE_EPOCH_RUN_ID:-$(date +%s)-$(head -c 4 /dev/urandom | od -An -tx1 | tr -d ' \n')}"
export EXTRACE_EPOCH_RUN_ID
echo "EXTRACE_EPOCH_RUN_ID=${EXTRACE_EPOCH_RUN_ID}"

PIDS=()

# Graceful shutdown: kill all child processes on SIGTERM/SIGINT
cleanup() {
    echo "Shutting down executor processes..."
    for pid in "${PIDS[@]}"; do
        kill "$pid" 2>/dev/null || true
    done
    wait
    echo "Executor stopped."
    exit 0
}
trap cleanup SIGTERM SIGINT

# --- Xvfb ---
# Clean stale X locks left by a prior boot whose Xvfb exited before the
# cleanup trap could run; otherwise the next launch sees `Server is already
# active for display 99` and the container enters a restart loop.
DISPLAY_NUM="${DISPLAY_VALUE#:}"
rm -f "/tmp/.X${DISPLAY_NUM}-lock" "/tmp/.X11-unix/X${DISPLAY_NUM}"

echo "Starting Xvfb on ${DISPLAY_VALUE} with screen ${SCREEN_VALUE}..."
Xvfb "${DISPLAY_VALUE}" -screen 0 "${SCREEN_VALUE}" -ac &
PIDS+=($!)

echo "Waiting for Xvfb to be ready..."
timeout 15s bash -c "until xdpyinfo -display ${DISPLAY_VALUE} &>/dev/null; do sleep 0.5; done" || {
    echo "ERROR: Xvfb failed to start within 15 s"
    exit 1
}

# --- Window manager ---
echo "Starting Openbox..."
openbox &
PIDS+=($!)

# --- VNC ---
echo "Starting x11vnc on port ${VNC_PORT_VALUE}..."
x11vnc -display "${DISPLAY_VALUE}" -forever -nopw -rfbport "${VNC_PORT_VALUE}" \
       -shared -xkb -noxrecord -noxfixes -noxdamage &
PIDS+=($!)

# Wait briefly so VNC socket is ready before noVNC connects
sleep 1

# --- noVNC ---
echo "Starting noVNC on port ${NOVNC_PORT_VALUE}..."
/usr/share/novnc/utils/launch.sh --vnc "${VNC_HOST_VALUE}:${VNC_PORT_VALUE}" \
                                 --listen "${NOVNC_PORT_VALUE}" &
PIDS+=($!)

# Verify noVNC is listening before continuing
echo "Waiting for noVNC to be ready..."
timeout 10s bash -c "until curl -sf http://localhost:${NOVNC_PORT_VALUE}/ >/dev/null 2>&1; do sleep 0.5; done" || {
    echo "WARNING: noVNC may not have started correctly on port ${NOVNC_PORT_VALUE}"
}

# --- Honeypot workspace ---
# ADR 0008: package-mode invocation; PYTHONPATH=/home is set in the image.
echo "Setting up developer honeypot environment..."
python3 -m executor.flows.playwright.workspace

# --- Harness integrity ---
if [ ! -f "${HARNESS_SHA256_MANIFEST}" ]; then
    echo "ERROR: Harness checksum manifest is missing: ${HARNESS_SHA256_MANIFEST}"
    exit 1
fi
echo "Verifying harness extension checksum manifest..."
if ! sha256sum --check --status "${HARNESS_SHA256_MANIFEST}"; then
    echo "ERROR: Harness extension checksum verification failed."
    exit 1
fi

# --- VS Code settings ---
VSCODE_SETTINGS_DIR="/home/executor/.vscode/User"
mkdir -p "${VSCODE_SETTINGS_DIR}"
cat > "${VSCODE_SETTINGS_DIR}/settings.json" <<'SETTINGS'
{
  "security.workspace.trust.enabled": false,
  "workbench.startupEditor": "none",
  "telemetry.telemetryLevel": "off",
  "update.mode": "none",
  "extensions.autoCheckUpdates": false,
  "extensions.autoUpdate": false,
  "files.watcherExclude": {
    "**/.git/objects/**": true,
    "**/.git/subtree-cache/**": true,
    "**/node_modules/**": true,
    "**/.hg/store/**": true,
    "**/.extrace-harness/**": true
  },
  "window.dialogStyle": "custom",
  "files.simpleDialog.enable": true
}
SETTINGS

# --- VS Code ---
# Delegated to launch_vscode.sh so reset_state.py can reuse the same launch
# command between analyses for a clean restart. The script prints the PID
# of the detached VS Code process on stdout.
VSCODE_LAUNCH_SCRIPT="${EXECUTOR_VSCODE_LAUNCH_SCRIPT:-/home/executor/container/launch_vscode.sh}"
VSCODE_LOG_LEVEL="${EXECUTOR_VSCODE_LOG_LEVEL:-trace}"
CDP_BANNER="${CDP_PORT:+localhost:${CDP_PORT}}"
CDP_BANNER="${CDP_BANNER:-disabled (set EXECUTOR_CDP_PORT to opt in)}"
echo "Starting VS Code (CDP: ${CDP_BANNER}, log level: ${VSCODE_LOG_LEVEL})..."
VSCODE_PID="$(EXECUTOR_CDP_PORT="${CDP_PORT}" \
              EXECUTOR_VSCODE_LOG_LEVEL="${VSCODE_LOG_LEVEL}" \
              bash "${VSCODE_LAUNCH_SCRIPT}")"
PIDS+=("${VSCODE_PID}")

# Wait for VS Code to initialise, then symlink the latest log directory
(
    for _ in $(seq 1 20); do
        LATEST_LOG=$(find /home/executor/.vscode/logs -maxdepth 1 -type d 2>/dev/null | sort | tail -1)
        if [ -n "${LATEST_LOG}" ] && [ -d "${LATEST_LOG}" ]; then
            ln -sfn "${LATEST_LOG}" /home/executor/.vscode/logs/latest
            echo "VS Code log dir symlinked: ${LATEST_LOG} -> /home/executor/.vscode/logs/latest"
            break
        fi
        sleep 1
    done
) &

echo "================================================"
echo " ExTrace Executor Ready"
echo " noVNC : http://localhost:${NOVNC_PORT_VALUE}"
echo " VNC   : ${VNC_HOST_VALUE}:${VNC_PORT_VALUE}"
echo " CDP   : ${CDP_BANNER}"
echo " Display: ${DISPLAY_VALUE} (${SCREEN_VALUE})"
echo "================================================"

# Keep container alive; wait allows trap to fire
wait
