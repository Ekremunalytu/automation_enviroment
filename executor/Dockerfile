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

# Install monitoring tools, X11/Xvfb stack, and utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
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
    # Utilities
    curl \
    wget \
    gnupg \
    ca-certificates \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js (required for VS Code extensions runtime)
RUN curl -fsSL https://deb.nodesource.com/setup_${EXECUTOR_NODE_MAJOR}.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install VS Code via direct .deb download
# Detect architecture: arm64 -> linux-deb-arm64, amd64 -> linux-deb-x64
RUN ARCH=$(dpkg --print-architecture) \
    && if [ "$ARCH" = "arm64" ]; then VSCODE_ARCH="linux-deb-arm64"; else VSCODE_ARCH="linux-deb-x64"; fi \
    && curl -fsSL -o /tmp/vscode.deb "https://update.code.visualstudio.com/latest/${VSCODE_ARCH}/${EXECUTOR_VSCODE_CHANNEL}" \
    && dpkg -i /tmp/vscode.deb || true \
    && apt-get update \
    && apt-get install -f -y --no-install-recommends \
    && rm /tmp/vscode.deb \
    && rm -rf /var/lib/apt/lists/*

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

# Copy startup script
COPY executor/start.sh /usr/local/bin/start.sh
RUN chmod +x /usr/local/bin/start.sh

USER executor
WORKDIR /workspace

ENV DISPLAY=${EXECUTOR_DEFAULT_DISPLAY} \
    DONT_PROMPT_WSL_INSTALL=1 \
    VSCODE_CLI_DISABLE_TELEMETRY=1

EXPOSE ${EXECUTOR_DEFAULT_NOVNC_PORT}

ENTRYPOINT ["/usr/local/bin/start.sh"]
