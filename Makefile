# =============================================================================
# ExTrace Makefile
# Usage: make <target>
# =============================================================================

VENV := .venv/bin
TEST_DB_WAIT_SECONDS ?= 3
UI_TYPES_PYTHON := $(if $(wildcard $(VENV)/python),$(VENV)/python,python)

# Tidy `docker-compose ps` table: drop the long image-digest / command / created
# columns that make the raw default output wrap and look ragged. Shared by
# `up`, `rebuild`, `up-debug`, and `ps`/`status`.
COMPOSE_PS_FORMAT := table {{.Name}}\t{{.Service}}\t{{.Status}}\t{{.Ports}}

ifneq (,$(wildcard .env))
include .env
export
endif

.PHONY: help env fix-eol venv-wsl install install-dev install-hooks lint lint-check markdownlint format typecheck \
        security test test-unit test-integration test-smoke test-security test-security-ci-guard test-security-live test-cov test-local test-ci check check-all all clean \
        dev dev-lan run build rebuild up up-debug down logs ps restart status \
        migrate migrate-create venv-check \
        exec-build exec-up exec-down exec-shell exec-test exec-run \
        static-build static-up static-down static-shell static-run-fixture \
        ui-build ui-up ui-down ui-types ui-types-check ui-boundaries \
        demo-canary demo-canary-offline

DEMO_CANARY_ID := extrace.t1-demo-runnable-canary
DEMO_CANARY_VERSION := 0.0.1
DEMO_CANARY_DIR := extensions/malicious/t1-demo-runnable-canary
DEMO_CANARY_CONTAINER_DIR := /home/executor/.vscode/extensions/$(DEMO_CANARY_ID)-$(DEMO_CANARY_VERSION)
DEMO_CANARY_TRIGGER := /extensions-input/malicious/t1-demo-runnable-canary/trigger_payload.json

# =============================================================================
# HELP
# =============================================================================

help:
	@echo "╔═══════════════════════════════════════════════════════════════════╗"
	@echo "║                    🔮 ExTrace Development Commands                 ║"
	@echo "╠═══════════════════════════════════════════════════════════════════╣"
	@echo "║                         📦 Setup                                   ║"
	@echo "║  env            │ Create .env from .env.example (if missing)      ║"
	@echo "║  fix-eol        │ Repair CRLF -> LF scripts (Windows/WSL clone)    ║"
	@echo "║  venv-wsl       │ Recreate a Windows-layout .venv (auto on WSL)    ║"
	@echo "║  install        │ Install production dependencies                 ║"
	@echo "║  install-dev    │ Install dev dependencies                        ║"
	@echo "║  install-hooks  │ Install pre-commit hooks                        ║"
	@echo "╠═══════════════════════════════════════════════════════════════════╣"
	@echo "║                       🔍 Code Quality                              ║"
	@echo "║  lint           │ Ruff linter (auto-fix)                          ║"
	@echo "║  format         │ Format code                                     ║"
	@echo "║  typecheck      │ mypy type checker                               ║"
	@echo "║  security       │ Bandit security check                           ║"
	@echo "║  test           │ Run pytest                                      ║"
	@echo "║  test-unit      │ Fast mocked/unit lane                           ║"
	@echo "║  test-integration │ DB-backed integration lane                    ║"
	@echo "║  test-smoke     │ Executor-backed smoke lane                      ║"
	@echo "║  test-security  │ W5 malicious-fixture hygiene and coverage lane  ║"
	@echo "║  test-security-live │ Reserved local-only live-sample lane        ║"
	@echo "║  test-cov       │ pytest + coverage                               ║"
	@echo "║  check          │ lint + type + test                              ║"
	@echo "║  all            │ format + lint + type + test                     ║"
	@echo "╠═══════════════════════════════════════════════════════════════════╣"
	@echo "║                       🐳 Docker (Short)                            ║"
	@echo "║  build          │ Build all images                                ║"
	@echo "║  rebuild        │ Rebuild all (no cache)                          ║"
	@echo "║  up             │ Start all containers                            ║"
	@echo "║  down           │ Stop all containers                             ║"
	@echo "║  restart        │ Rebuild + restart all                           ║"
	@echo "║  logs           │ Tail container logs                             ║"
	@echo "║  ps             │ Show container status                           ║"
	@echo "║  status         │ ps alias                                        ║"
	@echo "╠═══════════════════════════════════════════════════════════════════╣"
	@echo "║                     🔬 Executor                                    ║"
	@echo "║  exec-build     │ Build executor image                            ║"
	@echo "║  exec-up        │ Start executor                                  ║"
	@echo "║  exec-down      │ Stop executor                                   ║"
	@echo "║  exec-shell     │ Shell into executor                             ║"
	@echo "║  exec-test      │ Verify executor tools                           ║"
	@echo "║  exec-run       │ Run Playwright automation                       ║"
	@echo "╠═══════════════════════════════════════════════════════════════════╣"
	@echo "║                     🛡️  Static Analyzer (ES-2)                     ║"
	@echo "║  static-build   │ Build static-analyzer image                     ║"
	@echo "║  static-up      │ Start static-analyzer                           ║"
	@echo "║  static-down    │ Stop static-analyzer                            ║"
	@echo "║  static-shell   │ Shell into static-analyzer                      ║"
	@echo "║  static-run-fixture │ Run analyzer over a fixture (TARGET=dir)    ║"
	@echo "╠═══════════════════════════════════════════════════════════════════╣"
	@echo "║                     🤖 Simulations & Automation                    ║"
	@echo "║  sim-all        │ UI-stimulus stress: scenarios w/o target ext.   ║"
	@echo "║  sim-target     │ Target-extension smoke (TARGET=publisher.name)  ║"
	@echo "║  sim-demo       │ Start executor & run quick Playwright demo      ║"
	@echo "║  sim-list       │ List available scenarios                        ║"
	@echo "║  sim-run        │ Run specific scenario (use SCENARIO=name)       ║"
	@echo "║    NB: sim-*/exec-run use 'docker exec -i' (no TTY) so they       ║"
	@echo "║    run cleanly under CI/agent harness; 'exec-shell' keeps -it.    ║"
	@echo "║  demo-canary    │ Install & trigger safe runnable malicious demo  ║"
	@echo "║  demo-canary-offline │ Run demo fixture through detection engine  ║"
	@echo "╠═══════════════════════════════════════════════════════════════════╣"
	@echo "║                     🖥️  UI Dashboard                               ║"
	@echo "║  ui-build       │ Build UI image                                  ║"
	@echo "║  ui-up          │ Start UI container                              ║"
	@echo "║  ui-down        │ Stop UI container                               ║"
	@echo "║  ui-types       │ Generate backend-owned UI contract types        ║"
	@echo "║  ui-types-check │ Fail on generated UI contract drift             ║"
	@echo "║  ui-boundaries  │ Check UI feature boundary imports               ║"
	@echo "╠═══════════════════════════════════════════════════════════════════╣"
	@echo "║                     🗄️  Database                                   ║"
	@echo "║  migrate        │ Run Alembic migrations                          ║"
	@echo "║  migrate-create │ Create new migration                            ║"
	@echo "╠═══════════════════════════════════════════════════════════════════╣"
	@echo "║  dev            │ Local dev server (loopback, uvicorn --reload)   ║"
	@echo "║  dev-lan        │ Local dev server with EXTRACE_ALLOW_LAN=1       ║"
	@echo "║  up-debug       │ Compose up with `debug` profile (CDP exposed)   ║"
	@echo "║  clean          │ Clean cache / build files                       ║"
	@echo "╚═══════════════════════════════════════════════════════════════════╝"

# =============================================================================
# VIRTUAL ENVIRONMENT
# =============================================================================

venv-check:
	@if [ ! -d ".venv" ]; then \
		echo "❌ Virtual environment not found!"; \
		echo "   Run: python -m venv .venv"; \
		echo "   Then: source .venv/bin/activate && pip install -r requirements-dev.txt"; \
		exit 1; \
	else \
		echo "✅ Virtual environment found at .venv/"; \
	fi

# =============================================================================
# INSTALLATION
# =============================================================================

env:
	@if [ -f .env ]; then \
		echo "ℹ️  .env already exists — leaving it untouched."; \
	else \
		cp .env.example .env; \
		echo "✅ Created .env from .env.example (edit values as needed)."; \
	fi

# WSL / Windows-checkout helper. If the repo was cloned on Windows the tracked
# shell scripts can land as CRLF, which breaks the Linux-container entrypoints
# ("exec docker-entrypoint.sh: no such file or directory"). `.gitattributes`
# enforces LF on fresh checkouts; this target repairs a working tree that
# already has CRLF (run once after pulling .gitattributes, then rebuild images).
fix-eol:
	@echo "🔧 Normalizing CRLF -> LF on tracked shell/template scripts..."
	@changed=0; \
	for f in $$(git ls-files '*.sh' '*.bash' '*.template'); do \
		if file "$$f" | grep -q CRLF; then \
			sed -i 's/\r$$//' "$$f" && echo "  fixed: $$f" && changed=1; \
		fi; \
	done; \
	if [ "$$changed" = "0" ]; then echo "  (no CRLF found — nothing to do)"; fi
	@echo "✅ Line endings normalized. Rebuild affected images: make rebuild"

# Windows/WSL guard, runs before install / install-dev. A .venv created by a
# Windows Python has a Scripts/ layout (python.exe, no bin/python) that the
# Makefile's $(VENV)=.venv/bin paths cannot use, so install-dev's
# `.venv/bin/pip` fails. When that exact layout is detected the venv is
# recreated with the Linux interpreter. The guard is inert on macOS/Linux —
# a native .venv has no Scripts/ dir, so nothing here runs and those setups
# are left untouched.
venv-wsl:
	@if [ -d ".venv/Scripts" ] && [ ! -e ".venv/bin/python" ]; then \
		echo "🪟 Windows-layout .venv detected (no .venv/bin) — recreating as a Linux venv..."; \
		rm -rf .venv; \
		python3 -m venv .venv; \
		./.venv/bin/python -m pip install --upgrade pip; \
		echo "✅ Linux .venv ready at .venv/bin."; \
	fi

install: env venv-wsl
	$(VENV)/pip install -r docker/api/requirements.txt

install-dev: env venv-wsl
	$(VENV)/pip install -r docker/api/requirements.txt
	$(VENV)/pip install -r requirements-dev.txt

install-hooks: install-dev
	$(VENV)/pre-commit install
	$(VENV)/pre-commit install --hook-type commit-msg
	$(VENV)/pre-commit install --hook-type pre-push
	@echo "✅ Pre-commit hooks installed (commit, commit-msg, pre-push)!"

# =============================================================================
# CODE QUALITY
# =============================================================================

lint:
	@echo "🔍 Running Ruff linter (with auto-fix)..."
	$(VENV)/ruff check . --fix
	@echo "✅ Linting complete!"

lint-check:
	@echo "🔍 Running Ruff linter (check only, no fix)..."
	$(VENV)/ruff check .
	@echo "✅ Lint check complete!"

markdownlint:  ## Run markdownlint without auto-fix (CI-safe; matches pre-commit rule set, no mangle)
	@echo "🔍 Running markdownlint (no --fix; matches pre-commit rule set)..."
	@npx --yes markdownlint-cli@0.41.0 \
		--config .markdownlint.json \
		--ignore 'extensions/**' \
		--ignore 'alembic/README*' \
		--ignore 'documents/archive/**' \
		--ignore 'node_modules/**' \
		--ignore 'ui/node_modules/**' \
		--ignore '.venv/**' \
		'**/*.md'
	@echo "✅ Markdown lint check complete!"

format:
	@echo "🎨 Formatting code with Ruff..."
	$(VENV)/ruff format .
	@echo "✅ Formatting complete!"

typecheck:
	@echo "🔬 Running mypy type checker..."
	$(VENV)/mypy . --config-file=pyproject.toml --ignore-missing-imports
	@echo "✅ Type checking complete!"

security:
	@echo "🔐 Running Bandit security check..."
	$(VENV)/bandit -c pyproject.toml -r . -ll
	@echo "✅ Security check complete!"

# =============================================================================
# DEV SERVER
# =============================================================================

dev: env
	$(VENV)/uvicorn main:app --reload --host 127.0.0.1

dev-lan: env
	@echo "⚠️  ADR 0007 — LAN binding requested. Read documents/runbooks/lan-exposure.md first."
	EXTRACE_ALLOW_LAN=1 $(VENV)/uvicorn main:app --reload --host $${API_HOST:-0.0.0.0}

run:
	$(VENV)/uvicorn main:app --host 127.0.0.1

# =============================================================================
# TESTING
# =============================================================================

test:
	@echo "🧪 Running tests..."
	$(VENV)/pytest -v
	@echo "✅ Tests complete!"

test-unit:
	@echo "🧪 Running unit lane..."
	$(VENV)/pytest -v -m "not smoke and not requires_db and not integration"
	@echo "✅ Unit lane complete!"

test-integration:
	@echo "🧪 Running integration lane..."
	$(VENV)/pytest -v -m "(requires_db or integration) and not smoke"
	@echo "✅ Integration lane complete!"

test-smoke:
	@echo "🧪 Running smoke lane..."
	$(VENV)/pytest -v -m "smoke"
	@echo "✅ Smoke lane complete!"

test-arch-import-mode:  ## Container paket-mode invariant (ADR 0008 §6)
	@echo "🧪 Asserting container import-mode contract..."
	$(VENV)/pytest -v tests/architecture/test_container_entrypoint.py -m "smoke or integration or not smoke"
	@echo "✅ Container import-mode contract held."

test-security:
	@echo "🧪 Running security fixture lane..."
	$(VENV)/pytest -v \
		tests/security/test_fixture_hygiene.py \
		tests/security/test_rule_coverage.py \
		tests/security/rules \
		tests/security/test_rule_validation.py \
		tests/security/test_benign_silence.py \
		tests/security/test_unaccounted_dropout_surface.py \
		tests/security/test_sandbox_evasion_canary.py \
		tests/security/test_static_container_isolation.py \
		tests/security/test_semgrep_js_rules.py \
		tests/static_runtime/test_rule_inventory.py \
		tests/static_runtime/test_evaluation_determinism.py \
		tests/static_runtime/test_evaluation_manifest.py \
		tests/static_runtime/test_evaluation_metrics.py \
		tests/static_runtime/test_static_eval_cli.py \
		tests/static_runtime/test_scan_coverage.py \
		tests/static_runtime/test_artifacts.py \
		tests/static_runtime/test_s3_file_tree_heuristics.py \
		tests/static_runtime/test_s4_blacklisted_domain.py \
		tests/static_runtime/test_s5_network_indicators.py \
		tests/static_runtime/test_s12_invisible_unicode.py \
		tests/static_runtime/test_s13_native_node_loader.py \
		tests/static_runtime/test_s14_globalstate_dormancy.py \
		tests/platform/contracts/test_domain_indicators.py \
		tests/platform/security \
		tests/architecture/test_default_bindings.py \
		tests/architecture/test_dockerfile_digest_pin.py \
		tests/workflows/marketplace/test_vsix_hardening.py \
		tests/workflows/marketplace/test_decision_gate.py \
		tests/executor/security/test_uri_trigger_injection.py \
		tests/workflows/activation_reports/test_router_path_traversal.py
	@echo "✅ Security fixture lane complete!"

test-security-ci-guard:
	@if [ -z "$$CI" ]; then \
		echo "❌ test-security-ci-guard is CI-only."; \
		exit 1; \
	fi
	@echo "🔒 Verifying outbound egress is blocked for the security fixture lane..."
	@$(UI_TYPES_PYTHON) - <<-'PY'
	import socket

	targets = [("1.1.1.1", 443), ("8.8.8.8", 443)]
	allowed = []
	for host, port in targets:
	    try:
	        with socket.create_connection((host, port), timeout=3):
	            allowed.append(f"{host}:{port}")
	    except OSError:
	        continue

	if allowed:
	    raise SystemExit(
	        f"Outbound egress is still enabled for: {', '.join(allowed)}"
	    )

	print("✅ Security fixture lane confirmed: outbound egress is blocked.")
	PY

test-security-live:
	@if [ -n "$$CI" ]; then \
		echo "❌ Refusing to run live security fixtures in CI."; \
		exit 1; \
	fi
	@if [ "$$I_UNDERSTAND_THIS_IS_LIVE" != "1" ]; then \
		echo "❌ Live fixture execution requires I_UNDERSTAND_THIS_IS_LIVE=1."; \
		exit 1; \
	fi
	@echo "ℹ️  No T3 live fixtures are configured yet."

test-cov:
	@echo "🧪 Running tests with coverage..."
	$(VENV)/pytest --cov --cov-report=html --cov-report=term-missing
	@echo "✅ Coverage report generated in htmlcov/"

test-local:
	@echo "🐳 Starting test database container..."
	docker-compose up -d postgres_test
	@echo "⏳ Waiting for Test PostgreSQL to be healthy..."
	@for i in $$(seq 1 30); do \
		status=$$(docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}unknown{{end}}' automation_db_test 2>/dev/null || echo "missing"); \
		if [ "$$status" = "healthy" ]; then \
			break; \
		fi; \
		if [ "$$i" -eq 30 ]; then \
			echo "❌ postgres_test did not become healthy"; \
			exit 1; \
		fi; \
		sleep 1; \
	done
	@echo "🧪 Running tests..."
	$(VENV)/pytest -v
	@echo "✅ Tests complete!"

test-ci:
	@echo "🧪 Running CI tests with blocking smoke acceptance..."
	@echo "    (overrides pyproject default '-m not smoke' so smoke lane actually runs)"
	@echo "🐳 Building and starting executor container for smoke tests..."
	docker-compose up -d --build executor
	@echo "⏳ Waiting for executor to become healthy..."
	@for i in $$(seq 1 60); do \
		status=$$(docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}unknown{{end}}' automation_executor 2>/dev/null || echo "missing"); \
		if [ "$$status" = "healthy" ]; then \
			break; \
		fi; \
		if [ "$$i" -eq 60 ]; then \
			echo "❌ executor did not become healthy"; \
			exit 1; \
		fi; \
		sleep 2; \
	done
	$(VENV)/pytest -m "smoke or not smoke" --cov --cov-report=xml --cov-report=term-missing -v

# =============================================================================
# ALL CHECKS
# =============================================================================

check: lint typecheck test
	@echo ""
	@echo "═══════════════════════════════════════════════════════════════"
	@echo "✅ All checks passed!"
	@echo "═══════════════════════════════════════════════════════════════"

check-all: lint typecheck security ui-types-check ui-boundaries markdownlint test
	@echo ""
	@echo "═══════════════════════════════════════════════════════════════"
	@echo "✅ All checks (including security) passed!"
	@echo "═══════════════════════════════════════════════════════════════"

all: format lint typecheck test
	@echo ""
	@echo "═══════════════════════════════════════════════════════════════"
	@echo "🚀 All tasks completed successfully!"
	@echo "═══════════════════════════════════════════════════════════════"

# =============================================================================
# DOCKER — Short Commands
# =============================================================================

build: env
	@echo "🔨 Building all Docker images..."
	@BUILDKIT_PROGRESS=plain docker-compose build 2>&1
	@echo "✅ Build complete!"

rebuild: env
	@echo "🔨 Rebuilding all Docker images (no cache)..."
	@BUILDKIT_PROGRESS=plain docker-compose build --no-cache 2>&1
	@echo "🔄 Recreating containers to pick up the new images..."
	@docker-compose up -d --force-recreate
	@docker-compose ps --format "$(COMPOSE_PS_FORMAT)"
	@echo "✅ Rebuild + recreate complete!"

up: env
	@echo "🚀 Starting all containers..."
	@docker-compose up -d
	@docker-compose ps --format "$(COMPOSE_PS_FORMAT)"
	@echo "✅ All containers running!"

up-debug: env
	@echo "🐛 Starting containers with debug profile (CDP port 9222 exposed)..."
	@# W14-3 (M14b): explicitly set EXECUTOR_CDP_PORT so the executor's
	@# in-container VS Code attaches the --remote-debugging-port flag.
	@# Default `make up` leaves the env var empty and CDP stays closed.
	@EXECUTOR_CDP_PORT=9222 docker-compose --profile debug up -d
	@docker-compose --profile debug ps --format "$(COMPOSE_PS_FORMAT)"
	@echo "✅ Debug-profile containers running. CDP available on 127.0.0.1:9222."

down:
	@echo "🛑 Stopping all containers..."
	@docker-compose down --remove-orphans
	@echo "✅ All containers stopped!"

restart: build up
	@echo "🔄 Restart complete!"

extensions-reset:
	@./scripts/reset_extensions.sh

api-fresh: extensions-reset
	@echo "🚀 Cold-starting API (rebuild + migrate)..."
	@docker compose up -d --build api
	@docker exec automation_api alembic upgrade head
	@echo "✅ Fresh API ready (extensions disk + DB cleared, image rebuilt, migrations applied)."

logs:
	docker-compose logs -f --tail=100

ps:
	@docker-compose ps --format "$(COMPOSE_PS_FORMAT)"

status: ps

# =============================================================================
# DATABASE
# =============================================================================

migrate: env
	@echo "🔄 Running Alembic migrations..."
	$(VENV)/alembic upgrade head
	@echo "✅ Migrations complete!"

migrate-create:
	@read -p "Enter migration message: " msg; \
	$(VENV)/alembic revision --autogenerate -m "$$msg"

# =============================================================================
# EXECUTOR
# =============================================================================

exec-build:
	@echo "🔬 Building executor image..."
	docker-compose build executor
	@echo "✅ Executor image built!"

exec-up:
	@echo "🔬 Starting executor..."
	docker-compose up -d executor
	@echo "✅ Executor started!"

exec-down:
	@echo "🔬 Stopping executor..."
	docker-compose stop executor
	docker-compose rm -f executor
	@echo "✅ Executor stopped!"

exec-shell:
	docker exec -it automation_executor /bin/bash

exec-test:
	@echo "🔬 Verifying executor tools..."
	docker exec automation_executor code --version --no-sandbox
	docker exec automation_executor node --version
	docker exec automation_executor python3 --version
	docker exec automation_executor pip3 show playwright | grep Version
	docker exec automation_executor which tcpdump
	docker exec automation_executor which inotifywait
	docker exec automation_executor which strace
	docker exec automation_executor which Xvfb
	docker exec automation_executor which xdotool
	@echo "✅ All executor tools verified!"

exec-run:
	docker exec -e PYTHONUNBUFFERED=1 -i automation_executor python3 -m executor.flows.playwright.entrypoint --monitor

# =============================================================================
# STATIC ANALYZER (ES-2, ADR 0016)
# =============================================================================

# The per-Dockerfile allowlist (docker/static_analyzer/Dockerfile.dockerignore)
# that keeps the build context small is a BuildKit feature; compose v2 uses
# BuildKit by default, so a plain `docker-compose build` honors it (same as the
# top-level `make build`). For a no-cache clean rebuild, use `make rebuild`.
static-build:
	@echo "🛡️  Building static-analyzer image..."
	docker-compose build static_analyzer
	@echo "✅ Static-analyzer image built!"

static-up:
	@echo "🛡️  Starting static-analyzer..."
	docker-compose up -d static_analyzer
	@echo "✅ Static-analyzer started!"

static-down:
	@echo "🛡️  Stopping static-analyzer..."
	docker-compose stop static_analyzer
	docker-compose rm -f static_analyzer
	@echo "✅ Static-analyzer stopped!"

static-shell:
	docker exec -it automation_static_analyzer /bin/bash

# Run the static runtime over a fixture dir inside the container. TARGET is a
# container-side path (e.g. /extensions-input/<dir>). Inputs are regex-validated
# before they reach the `docker exec` argv (W14-3 pattern from sim-target).
static-run-fixture: static-up
	@if [ -z "$(TARGET)" ]; then \
		echo "❌ Provide TARGET. Usage: make static-run-fixture TARGET=/extensions-input/<dir> [RULES_VERSION=0.0.0] [BUDGET=30]"; \
		exit 1; \
	fi
	@printf '%s' "$(TARGET)" | grep -qE '^[A-Za-z0-9._/-]+$$' || { \
		echo "❌ TARGET must match [A-Za-z0-9._/-]+ (got: $(TARGET))"; exit 1; \
	}
	@if [ -n "$(RULES_VERSION)" ] && ! printf '%s' "$(RULES_VERSION)" | grep -qE '^[A-Za-z0-9._-]+$$'; then \
		echo "❌ RULES_VERSION must match [A-Za-z0-9._-]+ (got: $(RULES_VERSION))"; exit 1; \
	fi
	@if [ -n "$(BUDGET)" ] && ! printf '%s' "$(BUDGET)" | grep -qE '^[0-9]+$$'; then \
		echo "❌ BUDGET must be an integer (got: $(BUDGET))"; exit 1; \
	fi
	@echo "🛡️  Running static analyzer over $(TARGET)..."
	docker exec -e PYTHONUNBUFFERED=1 -i automation_static_analyzer python3 -m static_runtime \
		--vsix-dir "$(TARGET)" \
		--report-path "/results/static-report.json" \
		--rules-version "$(if $(RULES_VERSION),$(RULES_VERSION),0.0.0)" \
		--timeout-budget-s "$(if $(BUDGET),$(BUDGET),30)"

# Deterministic SMF corpus evaluation. The launcher only performs a docker exec;
# fixture source stays read-only and artifacts land under ignored output/.
static-eval: static-up
	@printf '%s' "$(if $(SPLIT),$(SPLIT),tuning)" | grep -qE '^(tuning|holdout|all)$$' || { \
		echo "❌ SPLIT must be tuning, holdout, or all"; exit 1; \
	}
	@if [ -n "$(BUDGET)" ] && ! printf '%s' "$(BUDGET)" | grep -qE '^[1-9][0-9]*$$'; then \
		echo "❌ BUDGET must be a positive integer (got: $(BUDGET))"; exit 1; \
	fi
	$(VENV)/python scripts/static_eval.py \
		--split "$(if $(SPLIT),$(SPLIT),tuning)" \
		--timeout-budget-s "$(if $(BUDGET),$(BUDGET),30)"

# =============================================================================
# SIMULATION / AUTOMATION
# =============================================================================

sim-all: exec-up
	@echo "🤖 Running UI-stimulus stress lane (no target extension)..."
	@echo "    NB: this answers 'does the UI engine run?' — NOT 'did a target extension activate?'."
	@echo "    Expected: target_extension_observed=false, run_quality=inconclusive."
	@echo "    For target-activation health use: make sim-target TARGET=publisher.name"
	docker exec -e PYTHONUNBUFFERED=1 -i automation_executor python3 -m executor.flows.playwright.entrypoint --monitor

sim-target: exec-up
	@if [ -z "$(TARGET)" ]; then \
		echo "❌ Please provide a TARGET. Usage: make sim-target TARGET=publisher.name [TRIGGERS=/path/to/payload.json] [SCENARIO=<name>]"; \
		exit 1; \
	fi
	@# W14-3 (U4-U12): validate operator-supplied variables before they
	@# flow into the `docker exec` command line. Make variables are NEVER
	@# shell-escaped by Make itself, so an unvalidated `TARGET=foo;rm -rf /`
	@# would word-split inside the recipe's shell and execute side
	@# commands. Restricting each variable to its expected character class
	@# (extension ids are `publisher.name`-shaped; scenario ids are
	@# alphanumeric+underscore; trigger paths are filesystem paths) keeps
	@# the unquoted positional pass below safe in addition to the
	@# defense-in-depth quoting.
	@printf '%s' "$(TARGET)" | grep -qE '^[A-Za-z0-9._-]+$$' || { \
		echo "❌ TARGET must match [A-Za-z0-9._-]+ (got: $(TARGET))"; exit 1; \
	}
	@if [ -n "$(SCENARIO)" ] && ! printf '%s' "$(SCENARIO)" | grep -qE '^[A-Za-z0-9_]+$$'; then \
		echo "❌ SCENARIO must match [A-Za-z0-9_]+ (got: $(SCENARIO))"; exit 1; \
	fi
	@if [ -n "$(TRIGGERS)" ] && ! printf '%s' "$(TRIGGERS)" | grep -qE '^[A-Za-z0-9./_-]+$$'; then \
		echo "❌ TRIGGERS must match [A-Za-z0-9./_-]+ (got: $(TRIGGERS))"; exit 1; \
	fi
	@echo "🤖 Running target-extension smoke for $(TARGET)..."
	docker exec -e PYTHONUNBUFFERED=1 -i automation_executor python3 -m executor.flows.playwright.entrypoint \
		--monitor \
		--target-extension-id "$(TARGET)" \
		$(if $(TRIGGERS),--triggers "$(TRIGGERS)",) \
		$(if $(SCENARIO),--scenario "$(SCENARIO)",)

sim-demo: exec-up
	@echo "🤖 Running quick demo scenario..."
	docker exec -e PYTHONUNBUFFERED=1 -i automation_executor python3 -m executor.flows.playwright.entrypoint --demo

sim-list:
	@echo "🤖 Listing available scenarios..."
	docker exec -e PYTHONUNBUFFERED=1 -i automation_executor python3 -m executor.flows.playwright.entrypoint --list

sim-run: exec-up
	@if [ -z "$(SCENARIO)" ]; then \
		echo "❌ Please provide a SCENARIO. Usage: make sim-run SCENARIO=coding_session"; \
		exit 1; \
	fi
	@# W14-3 (U4-U12): see sim-target above for the rationale. Scenario ids
	@# are alphanumeric+underscore by convention; reject everything else
	@# before letting the value reach `docker exec`.
	@printf '%s' "$(SCENARIO)" | grep -qE '^[A-Za-z0-9_]+$$' || { \
		echo "❌ SCENARIO must match [A-Za-z0-9_]+ (got: $(SCENARIO))"; exit 1; \
	}
	@echo "🤖 Running scenario: $(SCENARIO)..."
	docker exec -e PYTHONUNBUFFERED=1 -i automation_executor python3 -m executor.flows.playwright.entrypoint --monitor --scenario "$(SCENARIO)"

demo-canary: exec-up
	@echo "🤖 Installing safe runnable demo canary into executor..."
	docker exec -u root automation_executor bash -lc 'rm -rf "$(DEMO_CANARY_CONTAINER_DIR)" && mkdir -p "$(DEMO_CANARY_CONTAINER_DIR)"'
	docker cp "$(DEMO_CANARY_DIR)/." automation_executor:"$(DEMO_CANARY_CONTAINER_DIR)/"
	docker exec -u root automation_executor chown -R executor:executor "$(DEMO_CANARY_CONTAINER_DIR)"
	@echo "🤖 Triggering $(DEMO_CANARY_ID) command via Playwright..."
	docker exec -e PYTHONUNBUFFERED=1 automation_executor python3 -m executor.flows.playwright.entrypoint \
		--monitor \
		--skip-automation \
		--reload-before-run \
		--target-extension-id "$(DEMO_CANARY_ID)" \
		--triggers "$(DEMO_CANARY_TRIGGER)"

demo-canary-offline:
	@echo "🧪 Running safe demo canary offline detection fixture..."
	$(VENV)/pytest -q tests/security/test_rule_validation.py -k t1-demo-runnable-canary
	@echo "✅ Demo canary offline fixture passed."

# =============================================================================
# UI WEB CONSOLE
# =============================================================================

ui-build:
	@echo "🖥️ Building UI image..."
	docker-compose build ui
	@echo "✅ UI image built!"

ui-up:
	@echo "🖥️ Starting UI container..."
	docker-compose up -d ui
	@echo "✅ UI started!"

ui-down:
	@echo "🖥️ Stopping UI container..."
	docker-compose stop ui
	docker-compose rm -f ui
	@echo "✅ UI stopped!"

ui-types:
	$(UI_TYPES_PYTHON) scripts/generate_ui_contracts.py

ui-types-check:
	$(UI_TYPES_PYTHON) scripts/generate_ui_contracts.py --check

ui-boundaries:
	cd ui && npm run lint:boundaries

# =============================================================================
# CLEANUP
# =============================================================================

clean:
	@echo "🧹 Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	find . -type f -name "coverage.xml" -delete 2>/dev/null || true
	@echo "✅ Cleanup complete!"
