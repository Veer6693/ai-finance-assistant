#!/bin/bash
echo "🚀 Starting AI-Powered Personal Finance Assistant..."
echo "=================================================="

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down servers..."
    kill $(jobs -p) 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Check prerequisites
if [ ! -d "venv" ]; then
    echo "❌ Setup incomplete. Please run: ./scripts/setup.sh"
    exit 1
fi

if [ ! -d "frontend/node_modules" ]; then
    echo "❌ Frontend dependencies missing. Please run: ./scripts/setup.sh"
    exit 1
fi

# Start backend in background
echo "📡 Starting Backend Server..."
source venv/bin/activate
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 5

# Start frontend
echo "🖥️  Starting Frontend Server..."
cd frontend
npm start &
FRONTEND_PID=$!
cd ..

# Wait for user input to stop
echo ""
echo "✅ Both servers are running:"
echo "   - Backend API: http://localhost:8000"
echo "   - Frontend App: http://localhost:3000"
echo "   - API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all servers"

# Wait for background processes
wait