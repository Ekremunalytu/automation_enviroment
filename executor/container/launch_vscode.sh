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

# W14-3 (M14b): CDP is now strictly opt-in. The legacy "default-on 9222"
# behavior reachable from same-container analyzed extensions is gone; an
# operator who needs CDP must explicitly set EXECUTOR_CDP_PORT (the
# `make up-debug` lane in the Makefile sets it for the `debug` compose
# profile). Empty value below means "no remote debugging flag is passed
# to `code`", so VS Code starts without exposing the unauthenticated CDP
# interface that previously rode along even in default `make up`.
CDP_PORT="${EXECUTOR_CDP_PORT:-}"
VSCODE_LOG_LEVEL="${EXECUTOR_VSCODE_LOG_LEVEL:-trace}"
VSCODE_USER_DATA_DIR="${EXECUTOR_VSCODE_USER_DATA_DIR:-/home/executor/.vscode}"
HARNESS_EXT_PATH="${EXECUTOR_HARNESS_EXT_PATH:-/home/executor/flows/harness_extension}"
WORKSPACE_PATH="${EXECUTOR_WORKSPACE_PATH:-/workspace}"
HARNESS_SECRET_PATH="${EXECUTOR_HARNESS_SECRET_PATH:-/run/extrace/harness-secret}"
HARNESS_PYTHON_SECRET_PATH="${EXECUTOR_HARNESS_PYTHON_SECRET_PATH:-/results/_extrace_harness_python_secret}"

# W13-1 (Codex H6): generate a fresh per-launch HMAC secret and stage it
# on two paths before VS Code (and therefore the harness extension)
# starts. The harness reads + unlinks ${HARNESS_SECRET_PATH} the moment
# its activate() runs, before the Python orchestration installs the
# analyzed (target) extension; the same-UID target therefore never sees
# the secret on disk. ${HARNESS_PYTHON_SECRET_PATH} lives under /results
# (bind-mounted to the host) so the Python orchestration can read the
# value via the host filesystem and use it to verify HMAC nonces on
# stimulus markers. This script is invoked from both start.sh (boot)
# and executor.flows.playwright.reset_state (between scans), so each
# VS Code lifetime gets its own secret.
HARNESS_SECRET_VALUE="$(head -c 32 /dev/urandom | od -An -tx1 | tr -d ' \n')"
umask 077
mkdir -p "$(dirname "${HARNESS_SECRET_PATH}")"
# rm -f covers the reset path: on the second launch, a stale 0400 file
# from a prior boot (if the harness skipped its unlink, e.g. crash)
# would otherwise reject the truncating redirect.
rm -f "${HARNESS_SECRET_PATH}"
printf '%s' "${HARNESS_SECRET_VALUE}" > "${HARNESS_SECRET_PATH}"
chmod 0400 "${HARNESS_SECRET_PATH}"
mkdir -p "$(dirname "${HARNESS_PYTHON_SECRET_PATH}")"
rm -f "${HARNESS_PYTHON_SECRET_PATH}"
printf '%s' "${HARNESS_SECRET_VALUE}" > "${HARNESS_PYTHON_SECRET_PATH}"
chmod 0600 "${HARNESS_PYTHON_SECRET_PATH}"
unset HARNESS_SECRET_VALUE  # never let the value reach VS Code's child env

if ! command -v code >/dev/null 2>&1; then
    echo "ERROR: VS Code CLI binary 'code' is not installed in the executor image." >&2
    exit 1
fi

# ``setsid`` detaches from the controlling terminal so the child survives
# the caller exiting (matters when reset_state.py relaunches VS Code —
# otherwise the freshly-launched process would get SIGHUP'd along with
# the reset script).
# W14-3 (M14b): the CDP flag is conditionally appended only when
# ${CDP_PORT} is non-empty so VS Code stays unreachable on the debug
# port in default boots.
CDP_FLAG=()
if [ -n "${CDP_PORT}" ]; then
    CDP_FLAG=(--remote-debugging-port="${CDP_PORT}")
fi
setsid code --no-sandbox \
    --user-data-dir "${VSCODE_USER_DATA_DIR}" \
    --extensionDevelopmentPath="${HARNESS_EXT_PATH}" \
    "${CDP_FLAG[@]}" \
    --log "${VSCODE_LOG_LEVEL}" \
    "${WORKSPACE_PATH}" \
    </dev/null >/dev/null 2>&1 &

VSCODE_PID=$!
echo "${VSCODE_PID}"
