# =============================================================================
# ExTrace Makefile
# Usage: make <target>
# =============================================================================

VENV := .venv/bin
TEST_DB_WAIT_SECONDS ?= 3

ifneq (,$(wildcard .env))
include .env
export
endif

.PHONY: help install install-dev install-hooks lint lint-check format typecheck \
        security test test-cov test-local test-ci check check-all all clean \
        dev run build rebuild up down logs ps restart status \
        migrate migrate-create venv-check \
        exec-build exec-up exec-down exec-shell exec-test exec-run \
        ui-build ui-up ui-down

# =============================================================================
# HELP
# =============================================================================

help:
	@echo "╔═══════════════════════════════════════════════════════════════════╗"
	@echo "║                    🔮 ExTrace Development Commands                 ║"
	@echo "╠═══════════════════════════════════════════════════════════════════╣"
	@echo "║                         📦 Setup                                   ║"
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
	@echo "║                     🤖 Simulations & Automation                    ║"
	@echo "║  sim-all        │ Start executor & run all scenarios (monitor)    ║"
	@echo "║  sim-demo       │ Start executor & run quick Playwright demo      ║"
	@echo "║  sim-list       │ List available scenarios                        ║"
	@echo "║  sim-run        │ Run specific scenario (use SCENARIO=name)       ║"
	@echo "╠═══════════════════════════════════════════════════════════════════╣"
	@echo "║                     🖥️  UI Dashboard                               ║"
	@echo "║  ui-build       │ Build UI image                                  ║"
	@echo "║  ui-up          │ Start UI container                              ║"
	@echo "║  ui-down        │ Stop UI container                               ║"
	@echo "╠═══════════════════════════════════════════════════════════════════╣"
	@echo "║                     🗄️  Database                                   ║"
	@echo "║  migrate        │ Run Alembic migrations                          ║"
	@echo "║  migrate-create │ Create new migration                            ║"
	@echo "╠═══════════════════════════════════════════════════════════════════╣"
	@echo "║  dev            │ Local dev server (uvicorn --reload)             ║"
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

install:
	$(VENV)/pip install -r docker/api/requirements.txt

install-dev:
	$(VENV)/pip install -r docker/api/requirements.txt
	$(VENV)/pip install -r requirements-dev.txt

install-hooks: install-dev
	$(VENV)/pre-commit install
	$(VENV)/pre-commit install --hook-type commit-msg
	@echo "✅ Pre-commit hooks installed!"

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

dev:
	$(VENV)/uvicorn main:app --reload

run:
	$(VENV)/uvicorn main:app

# =============================================================================
# TESTING
# =============================================================================

test:
	@echo "🧪 Running tests..."
	$(VENV)/pytest -v
	@echo "✅ Tests complete!"

test-cov:
	@echo "🧪 Running tests with coverage..."
	$(VENV)/pytest --cov --cov-report=html --cov-report=term-missing
	@echo "✅ Coverage report generated in htmlcov/"

test-local:
	@echo "🐳 Starting test database container..."
	docker-compose up -d postgres_test
	@echo "⏳ Waiting for Test PostgreSQL to be ready..."
	@sleep $(TEST_DB_WAIT_SECONDS)
	@echo "🧪 Running tests..."
	$(VENV)/pytest -v || true
	@echo "✅ Tests complete!"

test-ci:
	@echo "🧪 Running CI tests (requires DATABASE_URL env var)..."
	$(VENV)/pytest --cov --cov-report=xml --cov-report=term-missing -v

# =============================================================================
# ALL CHECKS
# =============================================================================

check: lint typecheck test
	@echo ""
	@echo "═══════════════════════════════════════════════════════════════"
	@echo "✅ All checks passed!"
	@echo "═══════════════════════════════════════════════════════════════"

check-all: lint typecheck security test
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

build:
	@echo "🔨 Building all Docker images..."
	@BUILDKIT_PROGRESS=plain docker-compose build 2>&1
	@echo "✅ Build complete!"

rebuild:
	@echo "🔨 Rebuilding all Docker images (no cache)..."
	@BUILDKIT_PROGRESS=plain docker-compose build --no-cache 2>&1
	@echo "✅ Rebuild complete!"

up:
	@echo "🚀 Starting all containers..."
	@docker-compose up -d
	@docker-compose ps
	@echo "✅ All containers running!"

down:
	@echo "🛑 Stopping all containers..."
	@docker-compose down --remove-orphans
	@echo "✅ All containers stopped!"

restart: build up
	@echo "🔄 Restart complete!"

logs:
	docker-compose logs -f --tail=100

ps:
	@docker-compose ps

status: ps

# =============================================================================
# DATABASE
# =============================================================================

migrate:
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
	docker exec -e PYTHONUNBUFFERED=1 -it automation_executor python3 /home/executor/playwright/entrypoint.py --monitor

# =============================================================================
# SIMULATION / AUTOMATION
# =============================================================================

sim-all: exec-up
	@echo "🤖 Starting all simulations with monitoring..."
	docker exec -e PYTHONUNBUFFERED=1 -it automation_executor python3 /home/executor/playwright/entrypoint.py --monitor

sim-demo: exec-up
	@echo "🤖 Running quick demo scenario..."
	docker exec -e PYTHONUNBUFFERED=1 -it automation_executor python3 /home/executor/playwright/entrypoint.py --demo

sim-list:
	@echo "🤖 Listing available scenarios..."
	docker exec -e PYTHONUNBUFFERED=1 -it automation_executor python3 /home/executor/playwright/entrypoint.py --list

sim-run: exec-up
	@if [ -z "$(SCENARIO)" ]; then \
		echo "❌ Please provide a SCENARIO. Usage: make sim-run SCENARIO=coding_session"; \
		exit 1; \
	fi
	@echo "🤖 Running scenario: $(SCENARIO)..."
	docker exec -e PYTHONUNBUFFERED=1 -it automation_executor python3 /home/executor/playwright/entrypoint.py --monitor --scenario $(SCENARIO)

# =============================================================================
# UI DASHBOARD
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
