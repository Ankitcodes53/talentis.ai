#!/bin/bash

# ========================================================================
# Talentis.ai - Complete Setup Script with New Database Schema
# ========================================================================

echo "🚀 Setting up Talentis.ai with SQLAlchemy Database..."
echo "========================================================================"

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Backend setup
echo ""
echo "📦 Setting up backend with SQLAlchemy..."
cd backend

# Create virtual environment
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Created virtual environment"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ Backend dependencies installed"

cd ..

# Database setup with new schema
echo ""
echo "🗄️  Initializing database with SQLAlchemy models..."
cd db

# Run migration script
python migrate_db.py --create-tables

# Ask about sample data
echo ""
read -p "🌱 Would you like to seed the database with sample data? (yes/no): " seed_choice
if [ "$seed_choice" = "yes" ] || [ "$seed_choice" = "y" ]; then
    python migrate_db.py --seed-data
    echo "✅ Sample data seeded successfully"
fi

cd ..

# Frontend setup
echo ""
echo "⚛️  Setting up frontend..."
cd frontend

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is required but not installed."
    echo "Please install Node.js and npm, then run this script again."
    exit 1
fi

echo "✅ npm found: $(npm --version)"

# Install dependencies
npm install
echo "✅ Frontend dependencies installed"

cd ..

# Create environment files from examples
echo ""
echo "📝 Setting up environment files..."

if [ ! -f "backend/.env" ]; then
    cp backend/.env.example backend/.env
    echo "✅ Created backend/.env (please update with your settings)"
else
    echo "✅ backend/.env already exists"
fi

if [ ! -f "frontend/.env" ]; then
    cp frontend/.env.example frontend/.env
    echo "✅ Created frontend/.env (please update with your settings)"
else
    echo "✅ frontend/.env already exists"
fi

# Display database info
echo ""
echo "========================================================================"
echo "📊 Database Schema Information"
echo "========================================================================"
python db/migrate_db.py --info

echo ""
echo "========================================================================"
echo "✅ Setup complete!"
echo "========================================================================"
echo ""
echo "📚 Database Tables Created:"
echo "   • users - User accounts (employers & candidates)"
echo "   • job_descriptions - Job postings"
echo "   • candidates - Candidate profiles"
echo "   • matches - AI-powered job-candidate matches"
echo "   • interviews - Interview sessions with AI questions"
echo "   • payments - Payment transactions & subscriptions"
echo "   • analytics - ROI metrics & user analytics"
echo "   • bias_audit_logs - AI transparency & fairness tracking"
echo "   • system_config - System configuration"
echo ""
echo "🚀 To start the development servers:"
echo ""
echo "Backend (Terminal 1):"
echo "  cd backend && source venv/bin/activate && uvicorn main:app --reload"
echo ""
echo "Frontend (Terminal 2):"
echo "  cd frontend && npm run dev"
echo ""
echo "📖 Documentation:"
echo "  • Database Schema: db/SCHEMA_DOCUMENTATION.md"
echo "  • Migration Guide: db/README.md"
echo "  • API Docs (after starting backend): http://localhost:8000/docs"
echo ""
echo "🔧 Database Management Commands:"
echo "  python db/migrate_db.py --info          # Show database info"
echo "  python db/migrate_db.py --create-tables # Create tables"
echo "  python db/migrate_db.py --seed-data     # Add sample data"
echo "  python db/migrate_db.py --reset         # Reset database"
echo "  python db/migrate_db.py --migrate-info  # PostgreSQL migration guide"
echo ""
echo "========================================================================"
