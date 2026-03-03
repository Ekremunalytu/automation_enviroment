#!/bin/sh
set -e

# Align the container's docker group GID with the mounted socket's GID
# so that appuser can run "docker exec" without root privileges.
if [ -S /var/run/docker.sock ]; then
    SOCK_GID=$(stat -c '%g' /var/run/docker.sock 2>/dev/null || stat -f '%g' /var/run/docker.sock 2>/dev/null)
    if [ -n "$SOCK_GID" ] && [ "$SOCK_GID" != "0" ]; then
        groupmod -g "$SOCK_GID" docker 2>/dev/null || true
    fi
    # If GID is 0 (root), just add appuser to root group
    if [ "$SOCK_GID" = "0" ]; then
        usermod -aG root appuser 2>/dev/null || true
    fi
fi

# Drop to appuser and exec the CMD
exec gosu appuser "$@"
