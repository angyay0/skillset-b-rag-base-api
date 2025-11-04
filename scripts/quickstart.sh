#!/bin/bash

# Blinky Base API - Quick Start Script

set -e

echo "🚀 Blinky Base API - Quick Start"
echo "========================================"
echo ""

# Check Python version
echo "📋 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "   Python version: $python_version"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found!"
    echo "   Copying .env.example to .env..."
    cp .env.example .env
    echo "   ✓ Please edit .env with your credentials"
    echo ""
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt
echo "   ✓ Dependencies installed"
echo ""

# Check if PostgreSQL is running
echo "🗄️  Checking PostgreSQL..."
if command -v psql &> /dev/null; then
    echo "   ✓ PostgreSQL is installed"
    
    # Try to create database
    echo "   Creating database (if not exists)..."
    createdb blinky_db 2>/dev/null || echo "   Database already exists"
else
    echo "   ⚠️  PostgreSQL not found. Please install PostgreSQL first."
    echo "   macOS: brew install postgresql"
    echo "   Ubuntu: sudo apt-get install postgresql"
    exit 1
fi
echo ""

# Run migrations
echo "🔄 Running database migrations..."
alembic upgrade head
echo "   ✓ Migrations completed"
echo ""

# Initialize database
echo "🏗️  Initializing database..."
python3 scripts/init_db.py
echo ""

echo "✅ Setup complete!"
echo ""
echo "📝 Next steps:"
echo "   1. Edit .env with your credentials"
echo "   2. Run: python3 app_new.py"
echo "   3. Test: curl http://localhost:5003/health"
echo ""
echo "📚 Documentation:"
echo "   - README.md - General documentation"
echo "   - ARCHITECTURE.md - Architecture details"
echo "   - MIGRATION_GUIDE.md - Migration from old version"
echo ""
