# Makefile for Steel Chat AI Assistant - MVP Development
.PHONY: help test test-mvp test-smoke test-e2e test-unit test-integration test-quick test-ci install dev-install format lint type-check quality run dev clean coverage

# Default target
help:  ## Show this help message
	@echo "Steel Chat AI Assistant - MVP Development Commands"
	@echo "=================================================="
	@echo ""
	@echo "Testing Commands (MVP Optimized):"
	@echo "  test-mvp        Run MVP essential tests only"
	@echo "  test-smoke      Run smoke tests for quick validation"
	@echo "  test-critical   Run critical priority tests"
	@echo "  test-quick      Run quick tests (<1s each)"
	@echo "  test-e2e        Run E2E tests (essential only)"
	@echo "  test-unit       Run unit tests only"
	@echo "  test-ci         Run CI/CD test suite"
	@echo "  test-all        Run all tests (including slow ones)"
	@echo ""
	@echo "Development Commands:"
	@echo "  install         Install production dependencies"
	@echo "  dev-install     Install development dependencies"
	@echo "  run             Start production server"
	@echo "  dev             Start development server with hot reload"
	@echo "  format          Format code with black and isort"
	@echo "  lint            Run linting with flake8"
	@echo "  type-check      Run type checking with mypy"
	@echo "  quality         Run all quality checks"
	@echo "  coverage        Generate coverage report"
	@echo "  clean           Clean up generated files"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

# MVP Testing Commands - Optimized for development velocity
test-mvp:  ## Run MVP essential tests only (smoke + critical)
	@echo "🚀 Running MVP essential tests..."
	pytest -m "mvp or smoke or priority('critical')" --tb=short -v

test-smoke:  ## Run smoke tests for quick validation (30s max)
	@echo "💨 Running smoke tests..."
	pytest -m "smoke" --tb=line -q --timeout=30

test-critical:  ## Run critical priority tests
	@echo "🎯 Running critical tests..."
	pytest -m "priority('critical') and not slow and not flaky" -v

test-quick:  ## Run quick tests (<1s each) for rapid feedback
	@echo "⚡ Running quick tests..."
	pytest -m "quick or (smoke and not slow)" --tb=line -q

test-e2e:  ## Run E2E tests (essential only, no flaky tests)
	@echo "🔄 Running essential E2E tests..."
	pytest tests/e2e/ -m "not flaky and not post_mvp" -v --timeout=30

test-unit:  ## Run unit tests only
	@echo "🧪 Running unit tests..."
	pytest tests/unit/ -m "not slow" -v

test-integration:  ## Run integration tests (stable only)
	@echo "🔗 Running integration tests..."
	pytest tests/integration/ -m "not flaky and not slow" -v

test-ci:  ## Run CI/CD test suite (no flaky or post-MVP tests)
	@echo "🏗️ Running CI test suite..."
	pytest -m "not skip_mvp and not flaky and not post_mvp" --cov=src --cov-report=xml

test-all:  ## Run all tests including slow ones (use with caution)
	@echo "🌍 Running ALL tests..."
	pytest --tb=short

# Pre-commit validation
test-pre-commit:  ## Run pre-commit validation tests
	@echo "✅ Running pre-commit tests..."
	pytest -m "(smoke or quick) and not slow" --tb=line -q --timeout=10

# Development Commands
install:  ## Install production dependencies
	pip install -r requirements/base.txt

dev-install:  ## Install development dependencies
	pip install -r requirements/dev.txt
	pip install -e .

run:  ## Start production server
	python -m uvicorn src.main:app --host 0.0.0.0 --port 8000

dev:  ## Start development server with hot reload
	python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Code Quality Commands
format:  ## Format code with black and isort
	@echo "🎨 Formatting code..."
	black src/ tests/
	isort src/ tests/

lint:  ## Run linting with flake8
	@echo "🔍 Running linter..."
	flake8 src/ tests/

type-check:  ## Run type checking with mypy
	@echo "🔬 Running type checker..."
	mypy src/

quality:  ## Run all quality checks (format, lint, type-check)
	@echo "🎯 Running all quality checks..."
	make format
	make lint
	make type-check

# Coverage and Reporting
coverage:  ## Generate detailed coverage report
	@echo "📊 Generating coverage report..."
	pytest --cov=src --cov-report=html --cov-report=term-missing --cov-branch

coverage-mvp:  ## Generate coverage report for MVP tests only
	@echo "📊 Generating MVP coverage report..."
	pytest -m "mvp or smoke or priority('critical')" --cov=src --cov-report=html --cov-report=term-missing

# Utility Commands
clean:  ## Clean up generated files
	@echo "🧹 Cleaning up..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf dist/
	rm -rf build/

# Performance and stress testing (Post-MVP)
test-performance:  ## Run performance tests (Post-MVP)
	@echo "⚡ Running performance tests..."
	pytest -m "performance or benchmark" -v --timeout=60

test-stress:  ## Run stress tests (Post-MVP)
	@echo "💪 Running stress tests..."
	pytest -m "slow and performance" -v --timeout=300

# Docker commands (if using Docker)
docker-build:  ## Build Docker image
	docker build -t steel-chat-ai .

docker-run:  ## Run Docker container
	docker run -p 8000:8000 steel-chat-ai

docker-test:  ## Run tests in Docker container
	docker run --rm steel-chat-ai make test-mvp

# Database commands (if needed)
db-upgrade:  ## Upgrade database schema
	@echo "🗄️ Upgrading database..."
	alembic upgrade head

db-reset:  ## Reset database (development only)
	@echo "🔄 Resetting database..."
	alembic downgrade base
	alembic upgrade head

# Environment validation
check-env:  ## Check environment setup
	@echo "🔧 Checking environment..."
	@python -c "import sys; print(f'Python: {sys.version}')"
	@python -c "import pytest; print(f'pytest: {pytest.__version__}')"
	@python -c "import fastapi; print(f'FastAPI: {fastapi.__version__}')"
	@echo "Environment check complete ✅"

# Quick development workflow
dev-workflow:  ## Complete development workflow (format, lint, test-quick)
	@echo "🔄 Running development workflow..."
	make format
	make lint
	make test-quick
	@echo "Development workflow complete ✅"

# MVP validation workflow
mvp-validate:  ## Complete MVP validation (quality + essential tests)
	@echo "🎯 Running MVP validation..."
	make quality
	make test-mvp
	@echo "MVP validation complete ✅"
