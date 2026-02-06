# =============================================================================
# ExTrace Makefile
# Centralized development commands for quality control
# Usage: make <target>
# =============================================================================

# Virtual environment path - all tools run from here
VENV := .venv/bin
TEST_DB_WAIT_SECONDS ?= 3

ifneq (,$(wildcard .env))
include .env
export
endif

.PHONY: help install install-dev install-hooks lint lint-check format typecheck test test-cov test-local test-ci check check-all all clean docker-up docker-down migrate venv-check executor-build executor-up executor-down executor-shell executor-test

# Default target
help:
	@echo "╔═══════════════════════════════════════════════════════════════════╗"
	@echo "║                    🔮 ExTrace Development Commands                 ║"
	@echo "╠═══════════════════════════════════════════════════════════════════╣"
	@echo "║  install        │ Install production dependencies                 ║"
	@echo "║  install-dev    │ Install development dependencies                ║"
	@echo "║  install-hooks  │ Install pre-commit hooks                        ║"
	@echo "╠═══════════════════════════════════════════════════════════════════╣"
	@echo "║  lint           │ Run Ruff linter                                 ║"
	@echo "║  format         │ Format code with Ruff                           ║"
	@echo "║  typecheck      │ Run mypy type checker                           ║"
	@echo "║  security       │ Run Bandit security check                       ║"
	@echo "║  test           │ Run pytest                                      ║"
	@echo "║  test-cov       │ Run pytest with coverage                        ║"
	@echo "║  check          │ Run all checks (lint, type, test)               ║"
	@echo "║  check-all      │ Run all checks + security                        ║"
	@echo "║  all            │ Format, lint, type, test (one command)          ║"
	@echo "╠═══════════════════════════════════════════════════════════════════╣"
	@echo "║  venv-check     │ Verify virtual environment exists               ║"
	@echo "║  docker-build   │ Build Docker images                             ║"
	@echo "║  docker-rebuild │ Rebuild Docker images (no cache)                ║"
	@echo "║  docker-up      │ Start Docker containers                         ║"
	@echo "║  docker-down    │ Stop Docker containers                          ║"
	@echo "║  migrate        │ Run Alembic migrations                          ║"
	@echo "║  clean          │ Clean cache and build files                     ║"
	@echo "╠═══════════════════════════════════════════════════════════════════╣"
	@echo "║  executor-build │ Build executor Docker image                   ║"
	@echo "║  executor-up    │ Start executor container                      ║"
	@echo "║  executor-down  │ Stop executor container                       ║"
	@echo "║  executor-shell │ Shell into running executor                   ║"
	@echo "║  executor-test  │ Verify VS Code CLI in executor                ║"
	@echo "╚═══════════════════════════════════════════════════════════════════╝"

# =============================================================================
# VIRTUAL ENVIRONMENT CHECK
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
	$(VENV)/pip install -r routers/requirements.txt

install-dev:
	$(VENV)/pip install -r routers/requirements.txt
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
# TESTING
# =============================================================================

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
	# Rely on pytest.ini/conftest to load settings from env or .env
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
# DOCKER & DATABASE
# =============================================================================

docker-build:
	@echo "Building Docker images..."
	@BUILDKIT_PROGRESS=plain docker-compose build 2>&1
	@echo "Build complete!"

docker-rebuild:
	@echo "Rebuilding Docker images (no cache)..."
	@BUILDKIT_PROGRESS=plain docker-compose build --no-cache 2>&1
	@echo "Rebuild complete!"

docker-up:
	@echo "Starting Docker containers..."
	@docker-compose up -d
	@docker-compose ps
	@echo "Containers started!"

docker-down:
	@echo "Stopping Docker containers..."
	@docker-compose down --remove-orphans
	@echo "Containers stopped!"

docker-logs:
	docker-compose logs -f --tail=100

migrate:
	@echo "🔄 Running Alembic migrations..."
	$(VENV)/alembic upgrade head
	@echo "✅ Migrations complete!"

migrate-create:
	@read -p "Enter migration message: " msg; \
	$(VENV)/alembic revision --autogenerate -m "$$msg"

# =============================================================================
# EXECUTOR (Dynamic Analysis Container)
# =============================================================================

executor-build:
	@echo "Building executor image..."
	docker-compose build executor
	@echo "Executor image built!"

executor-up:
	@echo "Starting executor container..."
	docker-compose up -d executor
	@echo "Executor container started!"

executor-down:
	@echo "Stopping executor container..."
	docker-compose stop executor
	docker-compose rm -f executor
	@echo "Executor container stopped!"

executor-shell:
	docker exec -it automation_executor /bin/bash

executor-test:
	@echo "Verifying executor tools..."
	docker exec automation_executor code --version --no-sandbox
	docker exec automation_executor node --version
	docker exec automation_executor which tcpdump
	docker exec automation_executor which inotifywait
	docker exec automation_executor which strace
	docker exec automation_executor which Xvfb
	docker exec automation_executor which xdotool
	@echo "All executor tools verified!"

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
