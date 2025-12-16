# =============================================================================
# ExTrace Makefile
# Centralized development commands for quality control
# Usage: make <target>
# =============================================================================

# Virtual environment path - all tools run from here
VENV := .venv/bin

.PHONY: help install install-dev install-hooks lint lint-check format typecheck test test-cov test-local test-ci check check-all all clean docker-up docker-down migrate venv-check

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
	@echo "║  docker-up      │ Start Docker containers                         ║"
	@echo "║  docker-down    │ Stop Docker containers                          ║"
	@echo "║  migrate        │ Run Alembic migrations                          ║"
	@echo "║  clean          │ Clean cache and build files                     ║"
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
	@sleep 3
	@echo "🧪 Running tests..."
	DATABASE_URL=postgresql://postgres:postgres@localhost:5434/test_db $(VENV)/pytest -v || true
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

docker-up:
	@echo "🐳 Starting Docker containers..."
	docker-compose up -d
	@echo "✅ Containers started!"

docker-down:
	@echo "🐳 Stopping Docker containers..."
	docker-compose down
	@echo "✅ Containers stopped!"

docker-logs:
	docker-compose logs -f

migrate:
	@echo "🔄 Running Alembic migrations..."
	$(VENV)/alembic upgrade head
	@echo "✅ Migrations complete!"

migrate-create:
	@read -p "Enter migration message: " msg; \
	$(VENV)/alembic revision --autogenerate -m "$$msg"

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

# =============================================================================
# DEV SERVER
# =============================================================================

dev:
	$(VENV)/uvicorn main:app --reload --host 0.0.0.0 --port 8000

run:
	$(VENV)/uvicorn main:app --host 0.0.0.0 --port 8000
