#!/bin/bash

# Quick start script for Nextflow Chatbot (local development)
echo "Setting up Nextflow Chatbot for local development..."

# Backend setup
echo "Setting up backend..."
cd backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt
echo "Backend setup complete!"
echo "Run backend with: cd backend && source venv/bin/activate && uvicorn main:app --reload"
cd ..

# Frontend setup
echo "Setting up frontend..."
cd frontend
if [ ! -d "node_modules" ]; then
    npm install
fi
echo "Frontend setup complete!"
echo "Run frontend with: cd frontend && npm run dev"
cd ..

echo ""
echo "Setup complete!"
echo ""
echo "To run locally:"
echo "1. Start backend: cd backend && source venv/bin/activate && uvicorn main:app --reload"
echo "2. Start frontend: cd frontend && npm run dev"
echo ""
echo "Make sure to set GOOGLE service account details in config.yaml or environment variables."

