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
CDP_PORT="${EXECUTOR_CDP_PORT:-9222}"
STARTUP_SLEEP_SECONDS="${EXECUTOR_STARTUP_SLEEP_SECONDS:-1}"
PLAYWRIGHT_FLOW_DIR="${EXECUTOR_PLAYWRIGHT_FLOW_DIR:-/home/executor/flows/playwright}"

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
echo "Setting up developer honeypot environment..."
python3 "${PLAYWRIGHT_FLOW_DIR}/workspace.py"

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
  "extensions.autoUpdate": false
}
SETTINGS

# --- VS Code ---
VSCODE_LOG_LEVEL="${EXECUTOR_VSCODE_LOG_LEVEL:-trace}"
echo "Starting VS Code (CDP on localhost:${CDP_PORT}, log level: ${VSCODE_LOG_LEVEL})..."
code --no-sandbox \
    --user-data-dir /home/executor/.vscode \
    --extensionDevelopmentPath=/home/executor/flows/harness_extension \
    --remote-debugging-port="${CDP_PORT}" \
    --log "${VSCODE_LOG_LEVEL}" \
    /workspace &
PIDS+=($!)

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
echo " CDP   : localhost:${CDP_PORT}"
echo " Display: ${DISPLAY_VALUE} (${SCREEN_VALUE})"
echo "================================================"

# Keep container alive; wait allows trap to fire
wait
