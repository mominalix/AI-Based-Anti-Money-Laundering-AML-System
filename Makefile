.PHONY: help setup build run stop clean test logs health demo

# Default target
help:
	@echo "AML Microservices System"
	@echo "========================"
	@echo ""
	@echo "Available commands:"
	@echo "  make setup    - Setup environment configuration"
	@echo "  make run      - Start all services"
	@echo "  make stop     - Stop all services"
	@echo "  make build    - Build all Docker images"
	@echo "  make clean    - Clean up containers and volumes"
	@echo "  make test     - Run end-to-end tests"
	@echo "  make logs     - Show logs from all services"
	@echo "  make health   - Check health of all services"
	@echo "  make demo     - Run the demo workflow"
	@echo ""

# Setup environment configuration
setup:
	@echo "Setting up environment configuration..."
	@if [ ! -f .env ]; then \
		cp example.env.txt .env; \
		echo "Created .env file from example.env.txt"; \
		echo ""; \
		echo "IMPORTANT: Please edit .env file with your configuration:"; \
		echo "  - Set OPENAI_API_KEY for AI-powered SAR generation"; \
		echo "  - Set JWT_SECRET_KEY for authentication"; \
		echo "  - Adjust risk thresholds as needed"; \
		echo ""; \
	else \
		echo ".env file already exists"; \
	fi

# Build all Docker images
build:
	@echo "Building Docker images..."
	docker compose build

# Start all services
run:
	@echo "Starting AML microservices..."
	docker compose up -d
	@echo "Services starting... Use 'make health' to check status"

# Stop all services
stop:
	@echo "Stopping AML microservices..."
	docker compose down

# Clean up everything
clean:
	@echo "Cleaning up containers, networks, and volumes..."
	docker compose down -v --remove-orphans
	docker system prune -f

# Run end-to-end tests
test:
	@echo "Running end-to-end tests..."
	python tests/e2e/test_workflow.py

# Show logs from all services
logs:
	docker compose logs -f

# Check health of all services
health:
	@echo "Checking service health..."
	@echo "Gateway:        $$(curl -s http://localhost:8000/health | jq -r '.status' 2>/dev/null || echo 'DOWN')"
	@echo "Ingestion:      $$(curl -s http://localhost:8001/health | jq -r '.status' 2>/dev/null || echo 'DOWN')"
	@echo "Feature Engine: $$(curl -s http://localhost:8002/health | jq -r '.status' 2>/dev/null || echo 'DOWN')"
	@echo "Risk Scorer:    $$(curl -s http://localhost:8003/health | jq -r '.status' 2>/dev/null || echo 'DOWN')"
	@echo "Graph Analysis: $$(curl -s http://localhost:8004/health | jq -r '.status' 2>/dev/null || echo 'DOWN')"
	@echo "Alert Manager:  $$(curl -s http://localhost:8005/health | jq -r '.status' 2>/dev/null || echo 'DOWN')"

# Run the demo workflow
demo:
	@echo "Running AML demo workflow..."
	@echo "1. Uploading sample data..."
	curl -X POST http://localhost:8001/batch \
		-F "accounts=@fixtures/accounts.json" \
		-F "customers=@fixtures/customers.json" \
		-F "transactions=@fixtures/transactions.json"
	@echo ""
	@echo "2. Waiting for processing..."
	sleep 15
	@echo "3. Checking alerts..."
	curl -s http://localhost:8005/alerts | jq '.alerts | length' || echo "Error retrieving alerts"
	@echo ""
	@echo "4. Getting transaction details..."
	curl -s http://localhost:8002/features/T123 | jq '.features | keys | length' || echo "Error retrieving features"
	@echo ""
	@echo "Demo complete! Check the logs with 'make logs' for more details."

# Development helpers
dev-install:
	@echo "Installing development dependencies..."
	pip install -r requirements-dev.txt

lint:
	@echo "Running code linting..."
	flake8 services/
	black --check services/
	isort --check-only services/

format:
	@echo "Formatting code..."
	black services/
	isort services/

# Quick restart
restart: stop run

# Show service URLs
urls:
	@echo "Service URLs:"
	@echo "Gateway:        http://localhost:8000"
	@echo "Ingestion:      http://localhost:8001"
	@echo "Feature Engine: http://localhost:8002"
	@echo "Risk Scorer:    http://localhost:8003"
	@echo "Graph Analysis: http://localhost:8004"
	@echo "Alert Manager:  http://localhost:8005"
	@echo "RabbitMQ UI:    http://localhost:15672 (guest/guest)" 