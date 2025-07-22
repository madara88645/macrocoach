.PHONY: help install test lint format clean demo

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	poetry install
	poetry run pre-commit install

test: ## Run tests with coverage
	poetry run pytest --cov=src --cov-report=html --cov-report=term-missing

lint: ## Run linting
	poetry run ruff check src tests
	poetry run mypy src

format: ## Format code
	poetry run black src tests
	poetry run ruff --fix src tests

clean: ## Clean up cache and temporary files
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf htmlcov
	rm -rf dist
	rm -rf *.egg-info

demo: ## Start the demo with Docker Compose
	docker-compose up --build

dev: ## Start development server
	poetry run uvicorn src.macrocoach.main:app --reload --host 0.0.0.0 --port 8000

streamlit: ## Start Streamlit dashboard
	poetry run streamlit run src/macrocoach/ui/dashboard.py
