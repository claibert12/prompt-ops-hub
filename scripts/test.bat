@echo off
REM Prompt Ops Hub Test Script (Windows)
REM Runs tests with coverage and linting

echo 🧪 Running Prompt Ops Hub tests...

REM Run linting first
echo 🔍 Running Ruff linting...
python -m ruff check src/ tests/
if errorlevel 1 (
    echo ❌ Ruff linting failed
    exit /b 1
)

echo 🎨 Running Black formatting check...
python -m black --check src/ tests/
if errorlevel 1 (
    echo ❌ Black formatting check failed
    exit /b 1
)

echo 📝 Running MyPy type checking...
python -m mypy src/ --ignore-missing-imports
if errorlevel 1 (
    echo ❌ MyPy type checking failed
    exit /b 1
)

REM Run tests with coverage
echo 🧪 Running tests with coverage...
python -m pytest --cov=src --cov-report=term-missing --cov-report=html -v
if errorlevel 1 (
    echo ❌ Tests failed
    exit /b 1
)

echo ✅ All checks passed!
echo 📊 Coverage report generated in htmlcov/index.html 