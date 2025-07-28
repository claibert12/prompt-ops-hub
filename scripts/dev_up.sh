#!/bin/bash

# Development startup script for Prompt Ops Hub

set -e

echo "🚀 Starting Prompt Ops Hub development environment..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Create necessary directories
mkdir -p data
mkdir -p config

# Copy environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "📋 Creating .env file from template..."
    cp env.example .env
fi

# Start development services
echo "🐳 Starting development services with Docker Compose..."
docker-compose --profile dev up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if services are running
echo "🔍 Checking service status..."
docker-compose ps

# Run database migrations and seed data
echo "🗄️ Setting up database..."
docker-compose exec dev-api python -c "
from src.core.db import get_db_manager
db = get_db_manager()
db.create_tables()
print('✅ Database tables created')
"

# Seed demo data
echo "🌱 Seeding demo data..."
python scripts/seed_demo.py

echo "✅ Prompt Ops Hub development environment is ready!"
echo ""
echo "📊 Services:"
echo "  - API: http://localhost:8000"
echo "  - Frontend: http://localhost:3000"
echo "  - API Docs: http://localhost:8000/docs"
echo ""
echo "🔧 To stop services: docker-compose --profile dev down"
echo "📝 To view logs: docker-compose --profile dev logs -f" 