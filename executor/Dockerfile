# syntax=docker/dockerfile:1.7

# =============================================================================
# ExTrace Executor
# Dynamic analysis of VS Code extensions with full GUI via Xvfb + noVNC
# =============================================================================
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

ARG EXECUTOR_NODE_MAJOR=20
ARG EXECUTOR_VSCODE_CHANNEL=stable
ARG EXECUTOR_DEFAULT_DISPLAY=:99
ARG EXECUTOR_DEFAULT_NOVNC_PORT=6080

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

# Install VS Code via direct .deb download
# Detect architecture: arm64 -> linux-deb-arm64, amd64 -> linux-deb-x64
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    ARCH=$(dpkg --print-architecture) \
    && if [ "$ARCH" = "arm64" ]; then VSCODE_ARCH="linux-deb-arm64"; else VSCODE_ARCH="linux-deb-x64"; fi \
    && curl -fsSL -o /tmp/vscode.deb "https://update.code.visualstudio.com/latest/${VSCODE_ARCH}/${EXECUTOR_VSCODE_CHANNEL}" \
    && dpkg -i /tmp/vscode.deb || true \
    && apt-get update \
    && apt-get install -f -y --no-install-recommends \
    && rm -f /tmp/vscode.deb

# Install Playwright Python package and its system dependencies
COPY executor/requirements.txt /tmp/executor-requirements.txt
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

# Copy startup script
COPY executor/start.sh /usr/local/bin/start.sh
RUN chmod 755 /usr/local/bin/start.sh

# Copy Playwright automation scripts
COPY --chown=executor:executor executor/playwright /home/executor/playwright

USER executor
WORKDIR /workspace

ENV DISPLAY=${EXECUTOR_DEFAULT_DISPLAY} \
    DONT_PROMPT_WSL_INSTALL=1 \
    VSCODE_CLI_DISABLE_TELEMETRY=1

EXPOSE ${EXECUTOR_DEFAULT_NOVNC_PORT}

ENTRYPOINT ["/usr/local/bin/start.sh"]
