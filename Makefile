# =============================================================================
# ExTrace Makefile
# Centralized development commands for quality control
# Usage: make <target>
# =============================================================================

.PHONY: help install install-dev install-hooks lint format typecheck test test-cov test-local test-ci check clean docker-up docker-down migrate

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
	@echo "╠═══════════════════════════════════════════════════════════════════╣"
	@echo "║  docker-up      │ Start Docker containers                         ║"
	@echo "║  docker-down    │ Stop Docker containers                          ║"
	@echo "║  migrate        │ Run Alembic migrations                          ║"
	@echo "║  clean          │ Clean cache and build files                     ║"
	@echo "╚═══════════════════════════════════════════════════════════════════╝"

# =============================================================================
# INSTALLATION
# =============================================================================

install:
	pip install -r routers/requirements.txt

install-dev:
	pip install -r routers/requirements.txt
	pip install -r requirements-dev.txt

install-hooks: install-dev
	pre-commit install
	pre-commit install --hook-type commit-msg
	@echo "✅ Pre-commit hooks installed!"

# =============================================================================
# CODE QUALITY
# =============================================================================

lint:
	@echo "🔍 Running Ruff linter..."
	ruff check . --fix
	@echo "✅ Linting complete!"

format:
	@echo "🎨 Formatting code with Ruff..."
	ruff format .
	@echo "✅ Formatting complete!"

typecheck:
	@echo "🔬 Running mypy type checker..."
	mypy . --config-file=pyproject.toml --ignore-missing-imports
	@echo "✅ Type checking complete!"

security:
	@echo "🔐 Running Bandit security check..."
	bandit -c pyproject.toml -r . -ll
	@echo "✅ Security check complete!"

# =============================================================================
# TESTING
# =============================================================================

test:
	@echo "🧪 Running tests..."
	pytest -v
	@echo "✅ Tests complete!"

test-cov:
	@echo "🧪 Running tests with coverage..."
	pytest --cov --cov-report=html --cov-report=term-missing
	@echo "✅ Coverage report generated in htmlcov/"

test-local:
	@echo "🐳 Starting database container..."
	docker-compose up -d postgres
	@echo "⏳ Waiting for PostgreSQL to be ready..."
	@sleep 3
	@echo "🧪 Running tests..."
	DATABASE_URL=postgresql://postgres:1234@localhost:5433/postgres pytest -v || true
	@echo "✅ Tests complete!"

test-ci:
	@echo "🧪 Running CI tests (requires DATABASE_URL env var)..."
	pytest --cov --cov-report=xml --cov-report=term-missing -v

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
	alembic upgrade head
	@echo "✅ Migrations complete!"

migrate-create:
	@read -p "Enter migration message: " msg; \
	alembic revision --autogenerate -m "$$msg"

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
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

run:
	uvicorn main:app --host 0.0.0.0 --port 8000
