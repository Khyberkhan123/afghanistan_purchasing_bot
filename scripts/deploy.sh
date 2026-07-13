#!/bin/bash
# ─────────────────────────────────────────────────────────────
#  Production Deployment Script
# ─────────────────────────────────────────────────────────────
set -e

echo "🚀 Deploying Afghanistan Purchasing Bot..."

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "❌ Docker required"; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "❌ Docker Compose required"; exit 1; }

# Check .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found! Copy from .env.example and configure."
    exit 1
fi

# Pull latest changes (if git repo)
if [ -d .git ]; then
    git pull origin main
fi

# Build and start
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Wait for health check
echo "⏳ Waiting for health check..."
sleep 10

if docker-compose ps | grep -q "healthy"; then
    echo "✅ Bot deployed successfully!"
    echo "📊 Health: http://$(curl -s ifconfig.me):8080/health"
else
    echo "⚠️  Deployment may have issues. Check logs:"
    echo "   docker-compose logs -f bot"
fi
