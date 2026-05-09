#!/usr/bin/env bash
# Reset disk + DB extension state to a clean slate.
#
# Drops every extension directory / .vsix archive under ./extensions
# except the system index files, the canary `malicious/` folder, and the
# checked-in test fixtures (`extrace.fixture-*`); then deletes every row
# from the `extensions` table (FK CASCADE handles `extension_*` child
# tables). Test fixtures and the active in-flight scan version are NOT
# treated specially — invoke this only when you want a true cold start.
#
# Typical use:
#   make extensions-reset       # disk + DB only
#   make api-fresh              # extensions-reset + rebuild + migrate
#
# Safe to re-run; idempotent.

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXTENSIONS_DIR="$PROJECT_ROOT/extensions"

KEEP=(
  "extensions.json"
  "apiresponse.json"
  "malicious"
  "extrace.fixture-chat-0.0.1"
  "extrace.fixture-chat-0.0.1.vsix"
  "extrace.fixture-theme-0.0.1"
  "extrace.fixture-theme-0.0.1.vsix"
)

is_kept() {
  local name="$1"
  for k in "${KEEP[@]}"; do
    [[ "$name" == "$k" ]] && return 0
  done
  return 1
}

echo "Resetting extensions state (disk + DB)..."

# --- Disk ---
if [[ -d "$EXTENSIONS_DIR" ]]; then
  echo "  Disk: $EXTENSIONS_DIR"
  cd "$EXTENSIONS_DIR"
  shopt -s dotglob nullglob
  for entry in *; do
    if is_kept "$entry"; then
      echo "    keep: $entry"
    else
      if rm -rf -- "$entry" 2>/dev/null; then
        echo "    remove: $entry"
      else
        # Volume-mount edge case where rm fails on an empty-but-locked dir
        # (Docker bind-mount inconsistency, e.g. ".../<name> 2"). Try once
        # more with a force flag and fall through silently — the directory
        # is empty and does not consume catalog state.
        rm -rf --no-preserve-root -- "$entry" 2>/dev/null || \
          echo "    skip (locked): $entry"
      fi
    fi
  done
  shopt -u dotglob nullglob
  cd "$PROJECT_ROOT"
else
  echo "  Disk: $EXTENSIONS_DIR does not exist (nothing to do)."
fi

# --- DB ---
if docker ps --format '{{.Names}}' | grep -q '^automation_db$'; then
  echo "  DB: truncating extensions (CASCADE handles child rows)..."
  docker exec -i automation_db psql -U postgres -d postgres -v ON_ERROR_STOP=1 <<'SQL'
TRUNCATE TABLE extensions RESTART IDENTITY CASCADE;
SQL
  echo "  DB: extensions table cleared."
else
  echo "  DB: automation_db container not running — skipping table clear."
fi

echo "Done."
