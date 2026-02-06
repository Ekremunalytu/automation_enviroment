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
STARTUP_SLEEP_SECONDS="${EXECUTOR_STARTUP_SLEEP_SECONDS:-1}"

# Start virtual display
Xvfb "${DISPLAY_VALUE}" -screen 0 "${SCREEN_VALUE}" -ac &
sleep "${STARTUP_SLEEP_SECONDS}"

# Start window manager
openbox &
sleep "${STARTUP_SLEEP_SECONDS}"

# Start VNC server
x11vnc -display "${DISPLAY_VALUE}" -forever -nopw -rfbport "${VNC_PORT_VALUE}" -shared -quiet &
sleep "${STARTUP_SLEEP_SECONDS}"

# Start noVNC web client
/usr/share/novnc/utils/launch.sh --vnc "${VNC_HOST_VALUE}:${VNC_PORT_VALUE}" --listen "${NOVNC_PORT_VALUE}" &

echo "================================================"
echo " ExTrace Executor Ready"
echo " noVNC: http://${VNC_HOST_VALUE}:${NOVNC_PORT_VALUE}/vnc.html"
echo " Display: ${DISPLAY_VALUE} (${SCREEN_VALUE})"
echo "================================================"

# Keep container running
tail -f /dev/null
