# Makefile for AI Sports Model Builder

.PHONY: help clean test lint format docs setup dev-setup

# Variables
PYTHON = python
VENV = venv
PIP = $(VENV)/bin/pip
PYTEST = $(VENV)/bin/pytest
BLACK = $(VENV)/bin/black
ISORT = $(VENV)/bin/isort
FLAKE8 = $(VENV)/bin/flake8
MYPY = $(VENV)/bin/mypy
ALEMBIC = $(VENV)/bin/alembic

help:  ## Show this help message
	@echo 'Usage:'
	@echo '  make <target>'
	@echo ''
	@echo 'Targets:'
	@awk -F ':|##' '/^[^\t].+?:.*?##/ { printf "  %-20s %s\n", $$1, $$NF }' $(MAKEFILE_LIST)

clean:  ## Clean up Python cache files and build artifacts
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "*.egg" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type d -name "build" -exec rm -rf {} +
	find . -type d -name "dist" -exec rm -rf {} +

setup:  ## Set up Python virtual environment
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PIP) install -r requirements-dev.txt

dev-setup: setup  ## Set up development environment
	pre-commit install

test:  ## Run all tests
	$(PYTEST) tests/

test-unit:  ## Run unit tests
	$(PYTEST) tests/unit/

test-integration:  ## Run integration tests
	$(PYTEST) tests/integration/

test-functional:  ## Run functional tests
	$(PYTEST) tests/functional/

test-e2e:  ## Run end-to-end tests
	$(PYTEST) tests/e2e/

test-coverage:  ## Run tests with coverage report
	$(PYTEST) --cov=src --cov-report=term-missing --cov-report=html

lint:  ## Run linting
	$(FLAKE8) src tests
	$(MYPY) src tests

format:  ## Format code
	$(BLACK) src tests
	$(ISORT) src tests

format-check:  ## Check code formatting
	$(BLACK) --check src tests
	$(ISORT) --check-only src tests

db-init:  ## Initialize database
	$(PYTHON) src/core/database.py

db-migrate:  ## Run database migrations
	$(ALEMBIC) upgrade head

db-rollback:  ## Rollback last database migration
	$(ALEMBIC) downgrade -1

db-revision:  ## Create new database migration
	$(ALEMBIC) revision --autogenerate -m "$(message)"

docs:  ## Generate documentation
	mkdocs build

serve-docs:  ## Serve documentation locally
	mkdocs serve

ci:  ## Run all CI checks
	make clean
	make setup
	make format-check
	make lint
	make test-coverage

# Default target
.DEFAULT_GOAL := help 