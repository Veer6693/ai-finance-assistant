#!/bin/bash
echo "🚀 Starting Frontend Server..."
echo "=============================="

# Check if node_modules exists
if [ ! -d "frontend/node_modules" ]; then
    echo "❌ Frontend dependencies not found. Please run setup.sh first."
    exit 1
fi

# Navigate to frontend directory
cd frontend

# Start the React development server
echo "🖥️  Frontend starting on http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop the server"

npm start