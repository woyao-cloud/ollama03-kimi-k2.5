# Makefile for User Management API - Local Development

.PHONY: help install dev-install update-deps clean \
        db-start db-stop db-logs db-reset \
        migrate migrate-create migrate-rollback migrate-check \
        seed-db init-db \
        run run-dev debug \
        test test-unit test-integration test-cov test-watch \
        lint format check-types \
        api-docs shell \
        docker-build docker-up docker-down docker-logs

# =============================================================================
# Default Target
# =============================================================================

help: ## Show this help message
	@echo "User Management API - Development Commands"
	@echo "=========================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# =============================================================================
# Environment Setup
# =============================================================================

install: ## Install production dependencies
	pip install -e .

dev-install: ## Install development dependencies
	pip install -e ".[dev]"
	@echo "Installed with dev dependencies. Copy .env.example to .env and configure."

update-deps: ## Update all dependencies
	pip install --upgrade -e ".[dev]"

setup: dev-install ## Initial setup - install deps and configure
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "Created .env from .env.example - please edit with your settings"; \
	fi

# =============================================================================
# Database Operations (Docker)
# =============================================================================

db-start: ## Start PostgreSQL and Redis containers
	docker-compose up -d postgres redis
	@echo "Waiting for database to be ready..."
	@sleep 3
	@echo "Database started on localhost:5432"
	@echo "Redis started on localhost:6379"

db-stop: ## Stop all containers
	docker-compose down

db-logs: ## View database logs
	docker-compose logs -f postgres redis

db-reset: ## Reset database (WARNING: deletes all data)
	docker-compose down -v
	docker-compose up -d postgres redis
	@echo "Database reset complete. Run 'make migrate' to recreate tables."

db-shell: ## Open PostgreSQL shell
	docker-compose exec postgres psql -U devuser -d user_management

# =============================================================================
# Database Migrations
# =============================================================================

migrate: ## Run all pending migrations
	alembic upgrade head
	@echo "Migrations complete"

migrate-create: ## Create a new migration (usage: make migrate-create msg="add users table")
	alembic revision --autogenerate -m "$(msg)"

migrate-rollback: ## Rollback one migration
	alembic downgrade -1

migrate-check: ## Check current migration version
	alembic current

migrate-history: ## Show migration history
	alembic history --verbose

# =============================================================================
# Data Initialization
# =============================================================================

seed-db: ## Load seed data for development
	@python -c "import asyncio; from scripts.init_db import init_database; asyncio.run(init_database())"
	@echo "Seed data loaded"

init-db: migrate seed-db ## Initialize database with migrations and seed data

# =============================================================================
# Development Server
# =============================================================================

run: ## Run production server (requires db to be running)
	uvicorn app.main:app --host 0.0.0.0 --port 8000

run-dev: ## Run development server with auto-reload
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir app

debug: ## Run with debugpy for VS Code debugging
	python -m debugpy --listen 0.0.0.0:5678 --wait-for-client -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# =============================================================================
# Testing
# =============================================================================

test: ## Run all tests
	pytest -v

test-unit: ## Run unit tests only
	pytest tests/unit -v

test-integration: ## Run integration tests only
	pytest tests/integration -v -m "not slow"

test-cov: ## Run tests with coverage report
	pytest --cov=app --cov-report=term-missing --cov-report=html

test-watch: ## Run tests on file changes (requires pytest-watch)
	ptw -- --testmon

# =============================================================================
# Code Quality
# =============================================================================

lint: ## Run all linters (black, ruff, mypy)
	@echo "Running black..."
	black --check .
	@echo "Running ruff..."
	ruff check .
	@echo "Running mypy..."
	mypy app

format: ## Auto-format code with black and ruff
	@echo "Formatting with black..."
	black .
	@echo "Fixing with ruff..."
	ruff check --fix .

check-types: ## Type check with mypy
	mypy app

# =============================================================================
# Documentation
# =============================================================================

api-docs: ## Open API documentation in browser
	@echo "Swagger UI: http://localhost:8000/docs"
	@echo "ReDoc: http://localhost:8000/redoc"

# =============================================================================
# Docker Operations
# =============================================================================

docker-build: ## Build Docker images
	docker-compose build

docker-up: ## Start all services with docker-compose
	docker-compose up -d

docker-down: ## Stop all services
	docker-compose down

docker-logs: ## View all container logs
	docker-compose logs -f

# =============================================================================
# Utility
# =============================================================================

clean: ## Clean Python cache files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	@echo "Cleaned cache files"

shell: ## Open Python shell with app context
	python -c "import asyncio; from app.infrastructure.database.session import async_session; from app.domain.models import *; print('Shell ready with async support')" -i
