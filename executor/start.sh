#!/bin/bash
# =============================================================================
# ExTrace Executor Startup
# Starts Xvfb + Openbox + x11vnc + noVNC, then keeps container alive
# =============================================================================

# Start virtual display (1920x1080, 24-bit color)
Xvfb :99 -screen 0 1920x1080x24 -ac &
sleep 1

# Start window manager
openbox &
sleep 1

# Start VNC server (no password, listening on port 5900)
x11vnc -display :99 -forever -nopw -rfbport 5900 -shared -quiet &
sleep 1

# Start noVNC web client (browser access on port 6080)
/usr/share/novnc/utils/launch.sh --vnc localhost:5900 --listen 6080 &

echo "================================================"
echo " ExTrace Executor Ready"
echo " noVNC: http://localhost:6080/vnc.html"
echo " Display: :99 (1920x1080)"
echo "================================================"

# Keep container running
tail -f /dev/null
