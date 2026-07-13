#!/bin/bash
# ─────────────────────────────────────────────────────────────
#  Setup Script for New Installation
# ─────────────────────────────────────────────────────────────
set -e

echo "🔧 Setting up Afghanistan Purchasing Bot..."

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create directories
mkdir -p data logs

# Copy environment template
if [ ! -f .env ]; then
    echo "📝 Creating .env from template..."
    cp .env.example .env
    echo "⚠️  IMPORTANT: Edit .env with your BOT_TOKEN and ADMIN_IDS!"
fi

# Initialize database
echo "🗄️  Initializing database..."
python -c "
import asyncio
import sys
sys.path.insert(0, '.')
from bot.database import db
async def init():
    await db.connect()
    await db.init_schema()
    await db.close()
asyncio.run(init())
"

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit .env with your configuration"
echo "  2. Run: python main.py --polling"
echo "  3. Or for production: python main.py --webhook"
