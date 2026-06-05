#!/usr/bin/env bash
# =============================================================================
# ExTrace — air-gapped Podman controller (FEDORA SERVER target, rootful)
# -----------------------------------------------------------------------------
# Zero extra dependencies: needs ONLY `podman` (ships with Fedora Server). No
# compose, no internet. Run as root (rootful podman) — the api container drives
# its sibling containers through the rootful podman socket, mirroring the
# docker-compose `/var/run/docker.sock` orchestration.
#
# Commands:
#   load        podman load the bundled images + enable the rootful podman socket
#   up          create network + dirs, then start every service in order
#   down        stop + remove all ExTrace containers (volumes kept)
#   restart     down + up
#   status      podman ps for the ExTrace containers
#   logs [svc]  follow logs (svc = api|executor|static|ui|db; default api)
#   exec <svc> [cmd...]   exec into a container (default: bash)
#   migrate     run alembic migrations in the api container
#   destroy     down + remove the postgres data volume (DESTRUCTIVE)
#
# Tunables (env or edit here):
#   EXTRACE_BIND=127.0.0.1   host bind address. ADR 0007 default = loopback only.
#                            Set to 0.0.0.0 to expose on the LAN — only behind a
#                            firewall + after rotating POSTGRES_PASSWORD.
#   ENV_FILE=./extrace.env   path to the env file (defaults next to this script)
#   PODMAN_SOCK=/run/podman/podman.sock   rootful docker-compat socket
# =============================================================================
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$HERE}"
ENV_FILE="${ENV_FILE:-$PROJECT_DIR/extrace.env}"
IMAGES_TAR="${IMAGES_TAR:-$PROJECT_DIR/images.tar.gz}"
EXTRACE_BIND="${EXTRACE_BIND:-127.0.0.1}"
PODMAN_SOCK="${PODMAN_SOCK:-/run/podman/podman.sock}"
NET="extrace-net"
TAG="${TAG:-latest}"

IMG_API="localhost/extrace-api:$TAG"
IMG_EXECUTOR="localhost/extrace-executor:$TAG"
IMG_STATIC="localhost/extrace-static-analyzer:$TAG"
IMG_UI="localhost/extrace-ui:$TAG"
IMG_PG="localhost/extrace-postgres:16"

# Container names — these are CONTRACTUAL: executor/config.py hard-codes
# automation_executor / automation_static_analyzer, and the api reaches them by
# name via `docker exec`. Do not rename.
C_DB="automation_db"
C_API="automation_api"
C_EXEC="automation_executor"
C_STATIC="automation_static_analyzer"
C_UI="automation_ui"

log()  { printf '\033[1;36m[extrace]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[extrace] WARN:\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31m[extrace] ERROR:\033[0m %s\n' "$*" >&2; exit 1; }

need_root() { [ "$(id -u)" = "0" ] || die "run as root (rootful podman): sudo $0 $*"; }
have_podman() { command -v podman >/dev/null 2>&1 || die "podman not found (install it from the Fedora media)"; }

# Safe env reader — the env file contains values with spaces/&/: so it must NOT
# be `source`d. Pull single keys literally. (--env-file handles the full set for
# the containers; this is only for the handful the script needs locally.)
getenv() {
  local key="$1" def="${2:-}"
  local val
  val="$(grep -E "^${key}=" "$ENV_FILE" 2>/dev/null | tail -n1 | cut -d= -f2- || true)"
  [ -n "$val" ] && printf '%s' "$val" || printf '%s' "$def"
}

load_env() {
  [ -f "$ENV_FILE" ] || die "env file not found: $ENV_FILE (copy extrace.env and fill it in)"
  POSTGRES_USER="$(getenv POSTGRES_USER postgres)"
  POSTGRES_PASSWORD="$(getenv POSTGRES_PASSWORD postgres)"
  POSTGRES_DB="$(getenv POSTGRES_DB extrace)"
  POSTGRES_PORT="$(getenv POSTGRES_PORT 5432)"
  POSTGRES_DOCKER_PORT="$(getenv POSTGRES_DOCKER_PORT 5432)"
  POSTGRES_DOCKER_HOST="$(getenv POSTGRES_DOCKER_HOST postgres)"
  API_PORT="$(getenv API_PORT 8000)"
  API_WORKERS="$(getenv API_WORKERS 1)"
  EXEC_NOVNC_PORT="$(getenv EXECUTOR_NOVNC_PORT 6080)"
  EXEC_MEM="$(getenv EXECUTOR_MEM_LIMIT 4g)"
  EXEC_CPUS="$(getenv EXECUTOR_CPUS 2.0)"
  EXEC_SHM="$(getenv EXECUTOR_SHM_SIZE 1g)"
  STATIC_MEM="$(getenv STATIC_ANALYZER_MEM_LIMIT 1g)"
  STATIC_CPUS="$(getenv STATIC_ANALYZER_CPUS 1.0)"
  UI_PORT="$(getenv UI_PORT 3000)"
}

cmd_load() {
  need_root load
  have_podman
  [ -f "$IMAGES_TAR" ] || die "image tarball not found: $IMAGES_TAR"
  log "enabling rootful podman socket ($PODMAN_SOCK) …"
  systemctl enable --now podman.socket || warn "could not enable podman.socket via systemctl (continuing)"
  log "loading images from $IMAGES_TAR (large — be patient) …"
  podman load -i "$IMAGES_TAR"
  log "loaded:"
  podman images --filter 'reference=localhost/extrace-*' --format '  {{.Repository}}:{{.Tag}}  {{.Size}}'
}

ensure_net() {
  podman network exists "$NET" 2>/dev/null || { log "creating network $NET"; podman network create "$NET"; }
}

wait_pg() {
  log "waiting for postgres to accept connections …"
  for i in $(seq 1 60); do
    if podman exec "$C_DB" pg_isready -U "$POSTGRES_USER" -p "$POSTGRES_DOCKER_PORT" >/dev/null 2>&1; then
      log "postgres is ready."; return 0
    fi
    sleep 2
  done
  die "postgres did not become ready in time (check: podman logs $C_DB)"
}

rm_if_exists() { podman container exists "$1" 2>/dev/null && { log "removing stale $1"; podman rm -f "$1" >/dev/null; } || true; }

cmd_up() {
  need_root up
  have_podman
  load_env
  [ -S "$PODMAN_SOCK" ] || { log "podman socket missing — enabling it"; systemctl enable --now podman.socket || die "cannot enable podman.socket"; }

  mkdir -p "$PROJECT_DIR/extensions" "$PROJECT_DIR/extensions/offline" "$PROJECT_DIR/output"
  ensure_net

  if [ "$EXTRACE_BIND" != "127.0.0.1" ]; then
    warn "binding to $EXTRACE_BIND (NON-loopback). ADR 0007: only do this behind a firewall + after rotating POSTGRES_PASSWORD."
  fi

  # --- postgres -------------------------------------------------------------
  rm_if_exists "$C_DB"
  log "starting $C_DB …"
  podman run -d --name "$C_DB" --network "$NET" --network-alias postgres \
    --restart unless-stopped \
    --env-file "$ENV_FILE" \
    -p "${EXTRACE_BIND}:${POSTGRES_PORT}:${POSTGRES_DOCKER_PORT}" \
    -v postgres_data:/var/lib/postgresql/data \
    --health-cmd "pg_isready -U ${POSTGRES_USER} -p ${POSTGRES_DOCKER_PORT}" \
    --health-interval 10s --health-timeout 5s --health-retries 5 \
    "$IMG_PG" postgres -p "${POSTGRES_DOCKER_PORT}" >/dev/null
  wait_pg

  # --- api (orchestrator) ---------------------------------------------------
  # Mounts the rootful podman socket at the docker.sock path so the baked-in
  # docker CLI drives the sibling containers unchanged. label=disable lets the
  # confined api domain talk to the host socket under SELinux; the entrypoint
  # aligns appuser's group to the socket GID for DAC. no-new-privileges kept.
  rm_if_exists "$C_API"
  log "starting $C_API …"
  podman run -d --name "$C_API" --network "$NET" --network-alias api \
    --restart unless-stopped \
    --env-file "$ENV_FILE" \
    -e DATABASE_URL="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_DOCKER_HOST}:${POSTGRES_DOCKER_PORT}/${POSTGRES_DB}" \
    -p "${EXTRACE_BIND}:${API_PORT}:${API_PORT}" \
    -v "$PROJECT_DIR/extensions:/app/extensions:z" \
    -v "$PROJECT_DIR/output:/app/output:z" \
    -v "$ENV_FILE:/app/.env:z,ro" \
    -v "${PODMAN_SOCK}:/var/run/docker.sock" \
    --security-opt label=disable \
    --security-opt no-new-privileges=true \
    --cap-drop ALL --cap-add SETUID --cap-add SETGID \
    "$IMG_API" \
    uvicorn main:app --host 0.0.0.0 --port "${API_PORT}" --workers "${API_WORKERS}" >/dev/null

  # --- executor -------------------------------------------------------------
  # CDP forced OFF (-e EXECUTOR_CDP_PORT= overrides any env-file value).
  rm_if_exists "$C_EXEC"
  log "starting $C_EXEC …"
  podman run -d --name "$C_EXEC" --network "$NET" \
    --restart unless-stopped \
    --env-file "$ENV_FILE" \
    -e EXECUTOR_CDP_PORT= \
    -e EXECUTOR_EXTENSIONS_CONTAINER_PATH=/extensions-input \
    -e EXECUTOR_OUTPUT_CONTAINER_PATH=/results \
    -p "${EXTRACE_BIND}:${EXEC_NOVNC_PORT}:${EXEC_NOVNC_PORT}" \
    -v "$PROJECT_DIR/extensions:/extensions-input:ro,z" \
    -v "$PROJECT_DIR/output:/results:z" \
    --security-opt no-new-privileges=true \
    --cap-drop ALL --cap-add NET_RAW --cap-add SYS_PTRACE \
      --cap-add SETUID --cap-add SETGID --cap-add SETPCAP \
    --memory "$EXEC_MEM" --cpus "$EXEC_CPUS" --shm-size "$EXEC_SHM" \
    --health-cmd "curl -sf http://localhost:${EXEC_NOVNC_PORT}/ || exit 1" \
    --health-interval 15s --health-timeout 5s --health-retries 5 --health-start-period 30s \
    --stop-timeout 10 \
    "$IMG_EXECUTOR" >/dev/null

  # --- static analyzer (network-isolated) -----------------------------------
  rm_if_exists "$C_STATIC"
  log "starting $C_STATIC …"
  podman run -d --name "$C_STATIC" --network none \
    --restart unless-stopped \
    --env-file "$ENV_FILE" \
    -e EXECUTOR_EXTENSIONS_CONTAINER_PATH=/extensions-input \
    -e EXECUTOR_OUTPUT_CONTAINER_PATH=/results \
    -v "$PROJECT_DIR/extensions:/extensions-input:ro,z" \
    -v "$PROJECT_DIR/output:/results:z" \
    --security-opt no-new-privileges=true --cap-drop ALL \
    --memory "$STATIC_MEM" --cpus "$STATIC_CPUS" \
    --stop-timeout 5 \
    "$IMG_STATIC" sleep infinity >/dev/null

  # --- ui -------------------------------------------------------------------
  rm_if_exists "$C_UI"
  log "starting $C_UI …"
  podman run -d --name "$C_UI" --network "$NET" --network-alias ui \
    --restart unless-stopped \
    -e UI_PORT="${UI_PORT}" \
    -e API_BASE_URL= \
    -e API_PROXY_PASS="http://api:${API_PORT}" \
    -p "${EXTRACE_BIND}:${UI_PORT}:${UI_PORT}" \
    --security-opt no-new-privileges=true \
    --cap-drop ALL --cap-add SETUID --cap-add SETGID --cap-add CHOWN --cap-add DAC_OVERRIDE \
    "$IMG_UI" >/dev/null

  echo
  log "all services started."
  cmd_status
  echo
  log "UI:  http://${EXTRACE_BIND}:${UI_PORT}    API: http://${EXTRACE_BIND}:${API_PORT}/docs    noVNC: http://${EXTRACE_BIND}:${EXEC_NOVNC_PORT}"
  log "Drop extensions/.vsix into $PROJECT_DIR/extensions (offline VSIX → extensions/offline). Reports land in $PROJECT_DIR/output."
}

cmd_down() {
  need_root down
  have_podman
  for c in "$C_UI" "$C_STATIC" "$C_EXEC" "$C_API" "$C_DB"; do rm_if_exists "$c"; done
  log "stopped + removed all ExTrace containers (network + data volume kept)."
}

cmd_destroy() {
  need_root destroy
  cmd_down
  warn "removing postgres data volume (all scan history lost) …"
  podman volume rm postgres_data 2>/dev/null || true
  podman network rm "$NET" 2>/dev/null || true
  log "destroyed."
}

resolve_ctr() {
  case "$1" in
    api) echo "$C_API" ;; executor|exec) echo "$C_EXEC" ;;
    static) echo "$C_STATIC" ;; ui) echo "$C_UI" ;;
    db|postgres) echo "$C_DB" ;; *) echo "$1" ;;
  esac
}

cmd_status() { podman ps --filter "name=automation_" --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'; }
cmd_logs()   { podman logs -f --tail 100 "$(resolve_ctr "${1:-api}")"; }
cmd_exec()   { local c; c="$(resolve_ctr "${1:?usage: exec <svc> [cmd...]}")"; shift; podman exec -it "$c" "${@:-bash}"; }
cmd_migrate(){ need_root migrate; podman exec "$C_API" alembic upgrade head; }

case "${1:-}" in
  load)    cmd_load ;;
  up)      cmd_up ;;
  down)    cmd_down ;;
  restart) cmd_down; cmd_up ;;
  status)  cmd_status ;;
  logs)    shift; cmd_logs "$@" ;;
  exec)    shift; cmd_exec "$@" ;;
  migrate) cmd_migrate ;;
  destroy) cmd_destroy ;;
  *) cat <<EOF
ExTrace air-gapped Podman controller (rootful)

  sudo ./extrace-ctl.sh load        load images + enable podman socket (run once)
  sudo ./extrace-ctl.sh up          start all services
  sudo ./extrace-ctl.sh status      show container status
  sudo ./extrace-ctl.sh logs [svc]  follow logs (api|executor|static|ui|db)
  sudo ./extrace-ctl.sh exec <svc>  shell into a container
  sudo ./extrace-ctl.sh down        stop + remove containers (keep data)
  sudo ./extrace-ctl.sh restart     down + up
  sudo ./extrace-ctl.sh migrate     re-run DB migrations
  sudo ./extrace-ctl.sh destroy     remove containers + DB volume (DESTRUCTIVE)
EOF
    ;;
esac
