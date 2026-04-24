# syntax=docker/dockerfile:1.7

# =============================================================================
# ExTrace Executor
# Dynamic analysis of VS Code extensions with full GUI via Xvfb + noVNC
# Base image digest resolved on 2026-04-17 for deterministic W4/W5 builds.
# =============================================================================
FROM ubuntu:22.04@sha256:962f6cadeae0ea6284001009daa4cc9a8c37e75d1f5191cf0eb83fe565b63dd7

ENV DEBIAN_FRONTEND=noninteractive

ARG EXECUTOR_NODE_MAJOR
ARG EXECUTOR_VSCODE_CHANNEL
ARG EXECUTOR_VSCODE_VERSION
ARG EXECUTOR_DEFAULT_DISPLAY=:99
ARG EXECUTOR_DEFAULT_NOVNC_PORT=6080

RUN test -n "${EXECUTOR_NODE_MAJOR}" \
    && test -n "${EXECUTOR_VSCODE_CHANNEL}" \
    && test -n "${EXECUTOR_VSCODE_VERSION}"

# Install monitoring tools, X11/Xvfb stack, Python3, and utilities
# Cache apt indexes/packages between builds to reduce rebuild time.
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    echo "wireshark-common wireshark-common/install-setuid boolean false" | debconf-set-selections \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
    # Monitoring
    tcpdump \
    tshark \
    inotify-tools \
    strace \
    procps \
    net-tools \
    # Xvfb + GUI
    xvfb \
    x11vnc \
    novnc \
    openbox \
    xdotool \
    x11-utils \
    xterm \
    # Python3 (for Playwright automation)
    python3 \
    python3-pip \
    # Utilities
    curl \
    wget \
    gnupg \
    ca-certificates \
    sudo

# Install Node.js (required for VS Code extensions runtime)
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    curl -fsSL https://deb.nodesource.com/setup_${EXECUTOR_NODE_MAJOR}.x | bash - \
    && apt-get update \
    && apt-get install -y --no-install-recommends nodejs

# Install a pinned VS Code build via direct .deb download.
# Detect architecture: arm64 -> linux-deb-arm64, amd64 -> linux-deb-x64.
# Normalize env-sourced build args so inline dotenv comments or trailing
# whitespace cannot corrupt the download URL. Fail closed on embedded
# whitespace because the update endpoint expects exact path segments.
# Use apt to install the local .deb so dependency resolution and archive
# validation fail the build instead of silently continuing.
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    ARCH=$(dpkg --print-architecture) \
    && VSCODE_CHANNEL="$(printf '%s' "${EXECUTOR_VSCODE_CHANNEL}" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')" \
    && VSCODE_VERSION="$(printf '%s' "${EXECUTOR_VSCODE_VERSION}" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')" \
    && test -n "$VSCODE_CHANNEL" \
    && test -n "$VSCODE_VERSION" \
    && case "$VSCODE_CHANNEL" in *[[:space:]]*) echo "EXECUTOR_VSCODE_CHANNEL contains embedded whitespace: $VSCODE_CHANNEL" >&2; exit 1;; esac \
    && case "$VSCODE_VERSION" in *[[:space:]]*) echo "EXECUTOR_VSCODE_VERSION contains embedded whitespace: $VSCODE_VERSION" >&2; exit 1;; esac \
    && if [ "$ARCH" = "arm64" ]; then VSCODE_ARCH="linux-deb-arm64"; else VSCODE_ARCH="linux-deb-x64"; fi \
    && echo "Downloading VS Code ${VSCODE_VERSION} (${VSCODE_CHANNEL}) for ${VSCODE_ARCH}" \
    && curl --retry 5 --retry-all-errors --retry-delay 2 -fsSL -o /tmp/vscode.deb "https://update.code.visualstudio.com/${VSCODE_VERSION}/${VSCODE_ARCH}/${VSCODE_CHANNEL}" \
    && dpkg-deb --info /tmp/vscode.deb >/dev/null \
    && apt-get update \
    && apt-get install -y --no-install-recommends /tmp/vscode.deb \
    && command -v code >/dev/null \
    && rm -f /tmp/vscode.deb

# Install Playwright Python package and its system dependencies
COPY executor/container/requirements.txt /tmp/executor-requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/executor-requirements.txt \
    && playwright install-deps chromium \
    && rm /tmp/executor-requirements.txt

# Grant capture capabilities to non-root users
RUN setcap cap_net_raw+eip /usr/bin/tcpdump \
    && setcap cap_net_raw+eip /usr/bin/dumpcap

# Create non-root executor user
RUN useradd -m -s /bin/bash executor \
    && usermod -aG sudo executor

# Create working directories
RUN mkdir -p /workspace /results /extensions-input \
    && chown -R executor:executor /workspace /results /extensions-input

# Set up VS Code user data directory
RUN mkdir -p /home/executor/.vscode \
    && chown -R executor:executor /home/executor/.vscode

# Create index.html symlink for noVNC
RUN ln -s /usr/share/novnc/vnc.html /usr/share/novnc/index.html

# Copy startup + VS Code launch scripts (shared between boot and reset_state)
COPY executor/container/start.sh /usr/local/bin/start.sh
COPY executor/container/launch_vscode.sh /home/executor/container/launch_vscode.sh
RUN chmod 755 /usr/local/bin/start.sh /home/executor/container/launch_vscode.sh \
    && chown executor:executor /home/executor/container/launch_vscode.sh

# Copy Playwright automation scripts and shared contract package needed at runtime.
COPY --chown=executor:executor executor/flows /home/executor/flows
COPY --chown=executor:executor packages /home/packages
RUN find /home/executor/flows/harness_extension -type f -print0 \
    | LC_ALL=C sort -z \
    | xargs -0 sha256sum > /home/executor/flows/harness_extension.sha256 \
    && chown executor:executor /home/executor/flows/harness_extension.sha256

USER executor
WORKDIR /workspace

ENV DISPLAY=${EXECUTOR_DEFAULT_DISPLAY} \
    DONT_PROMPT_WSL_INSTALL=1 \
    VSCODE_CLI_DISABLE_TELEMETRY=1

EXPOSE ${EXECUTOR_DEFAULT_NOVNC_PORT}

ENTRYPOINT ["/usr/local/bin/start.sh"]
