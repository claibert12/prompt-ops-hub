# Makefile for Prompt Ops Hub

.PHONY: help install test lint clean dev-up dev-down seed-demo build-docker run-docker

help: ## Show this help message
	@echo "Prompt Ops Hub - Development Commands"
	@echo "====================================="
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install Python dependencies
	pip install -r requirements.txt

test: ## Run tests with coverage
	python -m pytest tests/ -v --cov=src --cov-report=html --cov-report=term

lint: ## Run linting checks
	ruff check src/ tests/
	ruff format --check src/ tests/

clean: ## Clean up generated files
	rm -rf __pycache__/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .ruff_cache/
	find . -name "*.pyc" -delete

dev-up: ## Start development environment
	@echo "🚀 Starting development environment..."
	docker-compose --profile dev up -d
	@echo "⏳ Waiting for services to be ready..."
	sleep 10
	@echo "🌱 Seeding demo data..."
	python scripts/seed_demo.py
	@echo "✅ Development environment ready!"
	@echo "📊 Services:"
	@echo "  - API: http://localhost:8000"
	@echo "  - Frontend: http://localhost:3000"
	@echo "  - API Docs: http://localhost:8000/docs"

dev-down: ## Stop development environment
	docker-compose --profile dev down

seed-demo: ## Seed demo data
	python scripts/seed_demo.py

build-docker: ## Build Docker images
	docker-compose build

run-docker: ## Run production Docker environment
	docker-compose up -d

stop-docker: ## Stop production Docker environment
	docker-compose down

logs: ## View logs
	docker-compose logs -f

api-logs: ## View API logs
	docker-compose logs -f dev-api

frontend-logs: ## View frontend logs
	docker-compose logs -f dev-frontend

agent-logs: ## View agent logs
	docker-compose logs -f dev-agent

test-agent: ## Test agent worker
	python -m src.agent.worker --poll-interval 5

test-api: ## Test API endpoints
	python -m pytest tests/test_main.py -v

test-integrity: ## Test integrity checks
	python -m pytest tests/test_observer.py -v

test-coverage: ## Test coverage checks
	python scripts/diff_coverage_check.py
	python scripts/trivial_test_check.py

format: ## Format code
	ruff format src/ tests/

check-all: ## Run all checks
	make lint
	make test
	make test-coverage

# Frontend commands
frontend-install: ## Install frontend dependencies
	cd frontend && npm install

frontend-dev: ## Start frontend development server
	cd frontend && npm run dev

frontend-build: ## Build frontend for production
	cd frontend && npm run build

frontend-test: ## Run frontend tests
	cd frontend && npm test 

# Development commands
dev-up:
	docker-compose -f docker-compose.yml up -d
	@echo "🚀 Development environment started"
	@echo "📊 API: http://localhost:8000"
	@echo "🎨 Frontend: http://localhost:3000"

dev-down:
	docker-compose -f docker-compose.yml down
	@echo "🛑 Development environment stopped"

# CI commands
ci-local: clean
	python -m pytest --cov=src --cov-report=xml --cov-report=term-missing
	python scripts/ci_self_check.py

all-green:
	python scripts/ci_self_check.py

policy-gate:
	python -c "from src.core.policy import policy_engine; from src.core.guardrails import guardrails; result = policy_engine.evaluate_policy({'coverage_threshold': 80, 'test_changes': [], 'integrity_violations': []}); violations = guardrails.check_policy_results({'allowed': result.allowed, 'violations': result.violations}); print('Policy check:', 'PASS' if result.allowed and not violations else 'FAIL'); exit(0 if result.allowed and not violations else 1)"

# Database commands
seed:
	python scripts/seed_demo.py
	@echo "🌱 Database seeded with demo data"

# Production commands
prod-up:
	docker-compose -f docker-compose.prod.yml up -d
	@echo "🚀 Production environment started"

prod-down:
	docker-compose -f docker-compose.prod.yml down
	@echo "🛑 Production environment stopped"

# Helm commands
helm-install:
	helm install prompt-ops-hub ./deploy/helm/prompt-ops-hub
	@echo "📦 Helm chart installed"

helm-upgrade:
	helm upgrade prompt-ops-hub ./deploy/helm/prompt-ops-hub
	@echo "📦 Helm chart upgraded"

helm-uninstall:
	helm uninstall prompt-ops-hub
	@echo "📦 Helm chart uninstalled"

# Integrity checks
integrity-check:
	python -c "from integrity_core import CoverageChecker, DiffCoverageChecker, TrivialTestChecker, TamperChecker, PolicyChecker; import sys; success, violations = CoverageChecker().check(); print('Coverage:', 'PASS' if success else 'FAIL'); success, violations = DiffCoverageChecker().check(); print('Diff Coverage:', 'PASS' if success else 'FAIL'); success, violations = TrivialTestChecker().check(); print('Trivial Tests:', 'PASS' if success else 'FAIL'); success, violations = TamperChecker().check(); print('Tamper Check:', 'PASS' if success else 'FAIL'); success, violations = PolicyChecker().check({}); print('Policy Check:', 'PASS' if success else 'FAIL')"

# Project initialization
init-project:
	@echo "Enter project name:"
	@read project_name; \
	po-cli init-project $$project_name

# Help
help:
	@echo "Available commands:"
	@echo "  dev-up          - Start development environment"
	@echo "  dev-down        - Stop development environment"
	@echo "  ci-local        - Run local CI checks"
	@echo "  seed            - Seed database with demo data"
	@echo "  prod-up         - Start production environment"
	@echo "  prod-down       - Stop production environment"
	@echo "  helm-install    - Install Helm chart"
	@echo "  helm-upgrade    - Upgrade Helm chart"
	@echo "  helm-uninstall  - Uninstall Helm chart"
	@echo "  integrity-check - Run all integrity checks"
	@echo "  init-project    - Initialize new project"
	@echo "  help            - Show this help"

.PHONY: dev-up dev-down ci-local seed prod-up prod-down helm-install helm-upgrade helm-uninstall integrity-check init-project help 