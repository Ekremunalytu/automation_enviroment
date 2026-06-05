#!/usr/bin/env bash
# =============================================================================
# ExTrace — air-gapped Podman bundle builder (BUILD MACHINE, needs internet)
# -----------------------------------------------------------------------------
# Builds all ExTrace images for the x86 (amd64) Fedora target, exports them as a
# single tarball with `docker save`, and assembles a self-contained bundle that
# you copy to the air-gapped Fedora Server. The server side needs ONLY podman
# (no compose, no internet, no extra packages).
#
# Run this on a machine WITH internet + docker:
#   - Apple Silicon Mac (arm64): auto cross-builds linux/amd64 via QEMU (slow
#     for the executor image — VS Code + Chromium under emulation).
#   - Native x86_64 Linux box (e.g. the ASUS TUF): builds amd64 natively, fast.
#
# Usage:
#   deploy/podman/build-bundle.sh
#
# Optional env overrides:
#   PLATFORM=linux/amd64   target arch (default linux/amd64 — DO NOT change for
#                          the x86 Fedora server)
#   TAG=latest             image tag
#   DIST_DIR=...           where to drop the bundle (default deploy/podman/dist)
#   ENGINE=docker          build engine (docker or podman)
# =============================================================================
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"

PLATFORM="${PLATFORM:-linux/amd64}"
TAG="${TAG:-latest}"
ENGINE="${ENGINE:-docker}"
DIST_DIR="${DIST_DIR:-$HERE/dist}"
STAGING="$DIST_DIR/staging"

# Pinned postgres digest — mirrors docker-compose.yml (ADR 0002 §4).
PG_REF="postgres:16-alpine@sha256:16bc17c64a573ef34162af9298258d1aec548232985b33ed7b1eac33ba35c229"

# Image tags baked into the bundle. The server-side controller (extrace-ctl.sh)
# expects exactly these names.
IMG_API="localhost/extrace-api:$TAG"
IMG_EXECUTOR="localhost/extrace-executor:$TAG"
IMG_STATIC="localhost/extrace-static-analyzer:$TAG"
IMG_UI="localhost/extrace-ui:$TAG"
IMG_PG="localhost/extrace-postgres:16"

log() { printf '\033[1;36m[build]\033[0m %s\n' "$*"; }
die() { printf '\033[1;31m[build] ERROR:\033[0m %s\n' "$*" >&2; exit 1; }

command -v "$ENGINE" >/dev/null 2>&1 || die "$ENGINE not found on PATH"

HOST_ARCH="$(uname -m)"
case "$HOST_ARCH" in
  x86_64|amd64) [ "$PLATFORM" = "linux/amd64" ] && log "native amd64 build (fast)" ;;
  arm64|aarch64) log "host is $HOST_ARCH; cross-building $PLATFORM via emulation (executor image will be SLOW)" ;;
esac

cd "$REPO"
mkdir -p "$STAGING"

# --- Build the four application images -------------------------------------
log "building api image …"
"$ENGINE" build --platform "$PLATFORM" -t "$IMG_API" -f docker/api/Dockerfile .

log "building executor image (heavy — VS Code/Chromium/Node/tshark) …"
"$ENGINE" build --platform "$PLATFORM" -t "$IMG_EXECUTOR" \
  --build-arg EXECUTOR_NODE_MAJOR=20 \
  --build-arg EXECUTOR_VSCODE_CHANNEL=stable \
  --build-arg EXECUTOR_VSCODE_VERSION=1.116.0 \
  --build-arg EXECUTOR_DEFAULT_DISPLAY=:99 \
  --build-arg EXECUTOR_DEFAULT_NOVNC_PORT=6080 \
  -f executor/container/Dockerfile .

log "building static-analyzer image …"
"$ENGINE" build --platform "$PLATFORM" -t "$IMG_STATIC" -f docker/static_analyzer/Dockerfile .

log "building ui image …"
"$ENGINE" build --platform "$PLATFORM" -t "$IMG_UI" -f ui/Dockerfile .

# --- Pull + retag postgres for the target arch ------------------------------
log "pulling postgres ($PLATFORM) …"
"$ENGINE" pull --platform "$PLATFORM" "$PG_REF"
"$ENGINE" tag "$PG_REF" "$IMG_PG"

# --- Export every image into one tarball ------------------------------------
log "saving images → images.tar (this is large; be patient) …"
"$ENGINE" save -o "$STAGING/images.tar" \
  "$IMG_API" "$IMG_EXECUTOR" "$IMG_STATIC" "$IMG_UI" "$IMG_PG"
log "compressing images.tar → images.tar.gz …"
gzip -f "$STAGING/images.tar"

# --- Assemble the server-side payload ---------------------------------------
log "assembling bundle payload …"
cp "$HERE/extrace-ctl.sh" "$STAGING/extrace-ctl.sh"
cp "$HERE/README.md" "$STAGING/README.md"
# Ship the NON-SECRET env template; operator fills secrets on the target.
cp "$REPO/.env.example" "$STAGING/extrace.env"

BUNDLE="$DIST_DIR/extrace-podman-bundle.tgz"
tar -C "$STAGING" -czf "$BUNDLE" .

log "done."
echo
echo "  Bundle: $BUNDLE"
echo "  Size:   $(du -h "$BUNDLE" | cut -f1)"
echo
echo "  Next:"
echo "    1. Copy it to the Fedora Server (USB / scp):"
echo "         scp \"$BUNDLE\" user@fedora-host:~/"
echo "    2. On the server:"
echo "         mkdir -p ~/extrace && tar -C ~/extrace -xzf ~/extrace-podman-bundle.tgz"
echo "         cd ~/extrace && sudo ./extrace-ctl.sh load && sudo ./extrace-ctl.sh up"
