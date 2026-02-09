#!/bin/bash
# =============================================================================
# ExTrace Executor Startup
# Starts Xvfb + Openbox + x11vnc + noVNC, then keeps container alive
# =============================================================================

set -euo pipefail

DISPLAY_VALUE="${EXECUTOR_DISPLAY:-${DISPLAY:-:99}}"
SCREEN_VALUE="${EXECUTOR_SCREEN:-1920x1080x24}"
VNC_HOST_VALUE="${EXECUTOR_VNC_HOST:-localhost}"
VNC_PORT_VALUE="${EXECUTOR_VNC_PORT:-5900}"
NOVNC_PORT_VALUE="${EXECUTOR_NOVNC_PORT:-6080}"
CDP_PORT="${EXECUTOR_CDP_PORT:-9222}"
STARTUP_SLEEP_SECONDS="${EXECUTOR_STARTUP_SLEEP_SECONDS:-1}"

echo "Starting Xvfb on ${DISPLAY_VALUE} with screen ${SCREEN_VALUE}..."
Xvfb "${DISPLAY_VALUE}" -screen 0 "${SCREEN_VALUE}" -ac &
XVFB_PID=$!

# Wait for Xvfb to be ready
echo "Waiting for Xvfb to be ready..."
timeout 10s bash -c "until xdpyinfo -display ${DISPLAY_VALUE} &>/dev/null; do sleep 0.5; done" || {
    echo "Xvfb failed to start"
    exit 1
}

echo "Starting Openbox..."
openbox &

echo "Starting x11vnc on port ${VNC_PORT_VALUE}..."
# Removed -quiet to see VNC logs
x11vnc -display "${DISPLAY_VALUE}" -forever -nopw -rfbport "${VNC_PORT_VALUE}" -shared &

echo "Setting up developer honeypot environment..."
python3 /home/executor/playwright/workspace.py

# Pre-configure VS Code: disable workspace trust, welcome tab, telemetry
VSCODE_SETTINGS_DIR="/home/executor/.vscode/User"
mkdir -p "${VSCODE_SETTINGS_DIR}"
cat > "${VSCODE_SETTINGS_DIR}/settings.json" <<'SETTINGS'
{
  "security.workspace.trust.enabled": false,
  "workbench.startupEditor": "none",
  "telemetry.telemetryLevel": "off",
  "update.mode": "none"
}
SETTINGS

echo "Starting VS Code (CDP on localhost:${CDP_PORT})..."
code --no-sandbox --user-data-dir /home/executor/.vscode --remote-debugging-port="${CDP_PORT}" /workspace &

echo "Starting noVNC on port ${NOVNC_PORT_VALUE}..."
/usr/share/novnc/utils/launch.sh --vnc "${VNC_HOST_VALUE}:${VNC_PORT_VALUE}" --listen "${NOVNC_PORT_VALUE}" &

echo "================================================"
echo " ExTrace Executor Ready"
echo " noVNC: http://localhost:${NOVNC_PORT_VALUE}/vnc.html"
echo " Display: ${DISPLAY_VALUE} (${SCREEN_VALUE})"
echo "================================================"

# Keep container running
tail -f /dev/null
