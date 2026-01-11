.PHONY: help install install-dev test lint format type-check security clean build upload pre-commit sonar sonar-start sonar-stop sonar-clean

help:  ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install the package
	pip install -e .

install-dev:  ## Install the package with development dependencies
	pip install -e ".[dev]"
	pip install -r requirements-dev.txt

test:  ## Run tests
	pytest tests/ --cov=financespy --cov-report=term-missing --cov-report=html

test-quick:  ## Run tests without coverage
	pytest tests/ -v

lint:  ## Run all linting tools
	ruff check .
	black --check .
	isort --check-only .
	flake8 financespy/

format:  ## Format code with black and isort
	black .
	isort .
	ruff check --fix .

type-check:  ## Run type checking with mypy
	mypy financespy/

security:  ## Run security checks
	bandit -r financespy/
	pip-audit --desc --requirement requirements-dev.txt

clean:  ## Clean up build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

build:  ## Build distribution packages
	python -m build

upload:  ## Upload to PyPI (requires twine)
	twine upload dist/*

pre-commit:  ## Install pre-commit hooks
	pre-commit install

pre-commit-run:  ## Run pre-commit on all files
	pre-commit run --all-files

check-all: lint type-check security test  ## Run all checks

ci: format check-all  ## Run CI pipeline locally

# SonarQube targets
sonar:  ## Start SonarQube and run analysis
	./sonar-analysis.sh

sonar-start:  ## Start SonarQube server only
	docker-compose up -d sonarqube db
	@echo "SonarQube starting... Check http://localhost:9000"

sonar-stop:  ## Stop SonarQube containers
	docker-compose down

sonar-clean:  ## Clean SonarQube analysis reports
	rm -f coverage.xml test-results.xml
	rm -f flake8-report.txt pylint-report.txt bandit-report.json
	rm -rf .scannerwork/ .sonar/