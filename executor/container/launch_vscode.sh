#!/bin/bash
# =============================================================================
# Launch (or re-launch) VS Code inside the executor container.
#
# Used by:
#   - ``start.sh`` during container boot (initial VS Code launch).
#   - ``executor/flows/playwright/reset_state.py`` between analyses (clean
#     restart once extensions/logs are cleared and the singleton lock is
#     removed), so the next ``code --install-extension`` talks to a fresh
#     instance instead of racing a stale IPC socket from the previous scan.
#
# The script is intentionally a thin wrapper: it only takes the same env
# vars start.sh relies on, starts VS Code detached in the background, and
# returns immediately. Callers wait for CDP readiness (the Playwright
# ``connect_to_ready_workbench`` helper or the start.sh log symlink watcher).
# =============================================================================

set -euo pipefail

CDP_PORT="${EXECUTOR_CDP_PORT:-9222}"
VSCODE_LOG_LEVEL="${EXECUTOR_VSCODE_LOG_LEVEL:-trace}"
VSCODE_USER_DATA_DIR="${EXECUTOR_VSCODE_USER_DATA_DIR:-/home/executor/.vscode}"
HARNESS_EXT_PATH="${EXECUTOR_HARNESS_EXT_PATH:-/home/executor/flows/harness_extension}"
WORKSPACE_PATH="${EXECUTOR_WORKSPACE_PATH:-/workspace}"

if ! command -v code >/dev/null 2>&1; then
    echo "ERROR: VS Code CLI binary 'code' is not installed in the executor image." >&2
    exit 1
fi

# ``setsid`` detaches from the controlling terminal so the child survives
# the caller exiting (matters when reset_state.py relaunches VS Code —
# otherwise the freshly-launched process would get SIGHUP'd along with
# the reset script).
setsid code --no-sandbox \
    --user-data-dir "${VSCODE_USER_DATA_DIR}" \
    --extensionDevelopmentPath="${HARNESS_EXT_PATH}" \
    --remote-debugging-port="${CDP_PORT}" \
    --log "${VSCODE_LOG_LEVEL}" \
    "${WORKSPACE_PATH}" \
    </dev/null >/dev/null 2>&1 &

VSCODE_PID=$!
echo "${VSCODE_PID}"
