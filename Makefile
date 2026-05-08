.PHONY: help setup dev-setup init-infra run-orchestrator test lint format docker-build docker-push deploy-k8s destroy coverage docs clean

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Install production dependencies
	pip install -r requirements.txt
	pre-commit install

dev-setup: ## Install development dependencies
	pip install -r requirements-dev.txt
	pre-commit install
	@echo "Development environment ready!"

init-infra: ## Initialize local infrastructure (Redis, Kafka, PostgreSQL)
	docker-compose up -d redis kafka postgres chromadb
	@echo "Waiting for services to be ready..."
	@sleep 10
	python scripts/init_db.py
	@echo "Infrastructure initialized!"

run-orchestrator: ## Start the orchestrator API
	uvicorn src.orchestrator.api:app --reload --host 0.0.0.0 --port 8000

run-workers: ## Start agent workers
	celery -A src.agents.worker worker --loglevel=info --concurrency=4

test: ## Run unit tests
	pytest tests/unit -v --tb=short

test-integration: ## Run integration tests
	pytest tests/integration -v --tb=short

test-load: ## Run load tests
	pytest tests/load -v --tb=short --workers=100

lint: ## Run linters
	black --check src/ tests/
	isort --check-only src/ tests/
	flake8 src/ tests/
	mypy src/

format: ## Format code
	black src/ tests/
	isort src/ tests/

coverage: ## Generate coverage report
	pytest --cov=src --cov-report=html --cov-report=term-missing
	@echo "Coverage report generated at htmlcov/index.html"

docker-build: ## Build Docker image
	docker build -t sales-agentic-army:latest -f docker/Dockerfile .

docker-push: ## Push Docker image to registry
	docker push sales-agentic-army:latest

deploy-k8s: ## Deploy to Kubernetes
	kubectl apply -k k8s/overlays/production
	@echo "Deployment initiated. Monitor with: kubectl get pods -n sales-system -w"

deploy-staging: ## Deploy to staging namespace
	kubectl apply -k k8s/overlays/staging

destroy: ## Destroy local infrastructure
	docker-compose down -v
	@echo "Infrastructure destroyed!"

docs: ## Build documentation
	mkdocs build
	@echo "Documentation built in site/"

docs-serve: ## Serve documentation locally
	mkdocs serve

clean: ## Clean build artifacts
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .pytest_cache/ .coverage htmlcov/
	@echo "Cleanup complete!"
