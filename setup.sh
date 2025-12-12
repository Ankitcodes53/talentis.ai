#!/bin/bash

# Setup script for Talentis.ai development environment

echo "🚀 Setting up Talentis.ai development environment..."

# Backend setup
echo ""
echo "📦 Setting up backend..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..

# Database setup
echo ""
echo "🗄️  Initializing database..."
cd db
python init_db.py
cd ..

# Frontend setup
echo ""
echo "⚛️  Setting up frontend..."
cd frontend
npm install
cd ..

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the development servers:"
echo ""
echo "Backend:  cd backend && source venv/bin/activate && uvicorn main:app --reload"
echo "Frontend: cd frontend && npm run dev"
echo ""
