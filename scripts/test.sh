#!/bin/bash

# Prompt Ops Hub Test Script
# Runs tests with coverage and linting

set -e

echo "🧪 Running Prompt Ops Hub tests..."

# Run linting first
echo "🔍 Running Ruff linting..."
python -m ruff check src/ tests/

echo "🎨 Running Black formatting check..."
python -m black --check src/ tests/

echo "📝 Running MyPy type checking..."
python -m mypy src/ --ignore-missing-imports

# Run tests with coverage
echo "🧪 Running tests with coverage..."
python -m pytest --cov=src --cov-report=term-missing --cov-report=html -v

echo "✅ All checks passed!"
echo "📊 Coverage report generated in htmlcov/index.html" 