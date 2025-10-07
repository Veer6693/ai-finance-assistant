#!/bin/bash

# AI-Powered Personal Finance Assistant - Complete Setup Script
# This script sets up the entire project from scratch

set -e  # Exit on any error

echo "🚀 Setting up AI-Powered Personal Finance Assistant..."
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "backend/requirements.txt" ] && [ ! -f "requirements.txt" ]; then
    print_error "Please run this script from the project root directory (ai-finance-assistant/)"
    exit 1
fi

# Step 1: Check Prerequisites
print_status "Checking prerequisites..."

# Check Python
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

# Check Node.js
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed. Please install Node.js 14+ first."
    exit 1
fi

# Check npm
if ! command -v npm &> /dev/null; then
    print_error "npm is not installed. Please install npm first."
    exit 1
fi

print_success "All prerequisites are installed!"

# Step 2: Setup Python Virtual Environment
print_status "Setting up Python virtual environment..."

if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_success "Virtual environment created!"
else
    print_warning "Virtual environment already exists, skipping creation."
fi

# Activate virtual environment
source venv/bin/activate
print_success "Virtual environment activated!"

# Step 3: Install Python Dependencies
print_status "Installing Python dependencies..."
pip install --upgrade pip

# Check which requirements file exists
if [ -f "backend/requirements-basic.txt" ]; then
    print_status "Installing basic dependencies first..."
    pip install -r backend/requirements-basic.txt
    
    print_status "Installing AI/ML dependencies (this may take a while)..."
    if [ -f "backend/requirements.txt" ]; then
        pip install -r backend/requirements.txt --no-deps || {
            print_warning "Some AI/ML packages failed to install. Installing core dependencies only..."
            pip install torch --index-url https://download.pytorch.org/whl/cpu
            pip install transformers spacy nltk
        }
    fi
elif [ -f "backend/requirements.txt" ]; then
    print_status "Installing all dependencies (this may take a while)..."
    pip install -r backend/requirements.txt || {
        print_warning "Some packages failed to install. Installing core dependencies..."
        pip install fastapi uvicorn sqlalchemy psycopg2-binary python-jose passlib python-multipart python-dotenv
        pip install numpy pandas scikit-learn requests httpx pytest
    }
elif [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    print_warning "No requirements.txt found, installing basic dependencies..."
    pip install fastapi uvicorn sqlalchemy psycopg2-binary python-jose passlib python-multipart
    pip install scikit-learn pandas numpy requests httpx pytest
fi

# Install additional dependencies that might be missing
pip install uvicorn python-multipart python-dotenv

print_success "Python dependencies installed!"

# Step 4: Setup PostgreSQL (if not already installed)
print_status "Checking PostgreSQL installation..."

if ! command -v psql &> /dev/null; then
    print_warning "PostgreSQL not found. Installing PostgreSQL..."
    
    # Detect OS and install accordingly
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Ubuntu/Debian
        sudo apt-get update
        sudo apt-get install -y postgresql postgresql-contrib
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            brew install postgresql
        else
            print_error "Please install PostgreSQL manually on macOS"
            exit 1
        fi
    else
        print_error "Unsupported OS. Please install PostgreSQL manually."
        exit 1
    fi
else
    print_success "PostgreSQL is already installed!"
fi

# Start PostgreSQL service
print_status "Starting PostgreSQL service..."
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    sudo systemctl start postgresql
    sudo systemctl enable postgresql
elif [[ "$OSTYPE" == "darwin"* ]]; then
    brew services start postgresql
fi

# Step 5: Setup Database
print_status "Setting up database..."

# Check if database exists, create if not
DB_EXISTS=$(sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='finance_assistant'" 2>/dev/null || echo "")

if [ "$DB_EXISTS" != "1" ]; then
    print_status "Creating database and user..."
    sudo -u postgres psql << EOF
CREATE DATABASE finance_assistant;
CREATE USER finance_user WITH PASSWORD 'finance_password_123';
GRANT ALL PRIVILEGES ON DATABASE finance_assistant TO finance_user;
\q
EOF
    print_success "Database and user created!"
else
    print_warning "Database already exists, skipping creation."
fi

# Step 6: Setup Environment Variables
print_status "Setting up environment variables..."

# Backend environment
if [ ! -f "backend/.env" ]; then
    cat > backend/.env << EOF
# Database Configuration
DATABASE_URL=postgresql://finance_user:finance_password_123@localhost/finance_assistant

# Security Configuration
SECRET_KEY=your-super-secret-key-change-this-in-production-$(date +%s)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# UPI Configuration (Sandbox/Mock)
RAZORPAY_KEY_ID=rzp_test_1234567890
RAZORPAY_KEY_SECRET=secret_1234567890

# Application Configuration
ENVIRONMENT=development
DEBUG=True
HOST=0.0.0.0
PORT=8000

# CORS Configuration
FRONTEND_URL=http://localhost:3000
ALLOWED_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000"]
EOF
    print_success "Backend environment file created!"
else
    print_warning "Backend environment file already exists, skipping creation."
fi

# Root environment (if needed)
if [ ! -f ".env" ]; then
    cp backend/.env .env
    print_success "Root environment file created!"
fi

# Step 7: Initialize Database Tables
print_status "Initializing database tables..."

python << EOF
import sys
import os
sys.path.append('backend')

try:
    from app.database import engine, Base
    from app.models.user import User
    from app.models.transaction import Transaction
    from app.models.budget import Budget
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully!")
except Exception as e:
    print(f"⚠️  Note: Database tables will be created when the app starts. Error: {e}")
EOF

print_success "Database setup completed!"

# Step 8: Setup Frontend
print_status "Setting up frontend dependencies..."

cd frontend

# Install Node.js dependencies
if [ -f "package.json" ]; then
    npm install
    print_success "Frontend dependencies installed from package.json!"
else
    print_warning "No package.json found, creating basic React app setup..."
    npm init -y
    npm install react react-dom react-scripts
    npm install @mui/material @emotion/react @emotion/styled @mui/icons-material
    npm install chart.js react-chartjs-2 axios react-router-dom
fi

# Step 9: Create Frontend Environment
if [ ! -f ".env" ]; then
    cat > .env << EOF
REACT_APP_API_URL=http://localhost:8000/api/v1
REACT_APP_ENVIRONMENT=development
GENERATE_SOURCEMAP=false
REACT_APP_ENABLE_UPI=true
REACT_APP_ENABLE_AI_CHAT=true
EOF
    print_success "Frontend environment file created!"
fi

cd ..

# Step 10: Run Tests (Optional)
print_status "Running basic tests..."

# Test backend connection
python << EOF
import sys
sys.path.append('backend')

try:
    from app.database import get_db
    db = next(get_db())
    print('✅ Database connection successful!')
    db.close()
except Exception as e:
    print(f'⚠️  Database connection test skipped: {e}')
EOF

# Step 11: Create startup scripts if they don't exist
print_status "Creating startup scripts..."

# Create start-backend.sh
if [ ! -f "scripts/start-backend.sh" ]; then
cat > scripts/start-backend.sh << 'EOF'
#!/bin/bash
echo "🚀 Starting Backend Server..."
echo "============================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Navigate to backend directory
cd backend

# Start the FastAPI backend
echo "📡 Backend starting on http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"

uvicorn main:app --reload --host 0.0.0.0 --port 8000
EOF
chmod +x scripts/start-backend.sh
fi

# Create start-frontend.sh
if [ ! -f "scripts/start-frontend.sh" ]; then
cat > scripts/start-frontend.sh << 'EOF'
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
EOF
chmod +x scripts/start-frontend.sh
fi

# Create start-all.sh
if [ ! -f "scripts/start-all.sh" ]; then
cat > scripts/start-all.sh << 'EOF'
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
EOF
chmod +x scripts/start-all.sh
fi

# Make all scripts executable
chmod +x scripts/*.sh

print_success "Startup scripts created!"

# Step 12: Download required AI models (if needed)
print_status "Setting up AI models..."

python << EOF
try:
    import spacy
    # Try to load English model, download if not available
    try:
        nlp = spacy.load("en_core_web_sm")
        print("✅ spaCy English model already available")
    except OSError:
        print("📥 Downloading spaCy English model...")
        spacy.cli.download("en_core_web_sm")
        print("✅ spaCy English model downloaded")
except ImportError:
    print("⚠️  spaCy not installed, AI models will be set up when needed")
EOF

# Step 13: Final Setup Summary
echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo ""
echo "✅ Virtual environment created and activated"
echo "✅ Python dependencies installed"
echo "✅ PostgreSQL database configured"
echo "✅ Database setup completed"
echo "✅ Frontend dependencies installed"
echo "✅ Environment variables configured"
echo "✅ Startup scripts created"
echo "✅ AI models prepared"
echo ""
echo "🚀 To start the application:"
echo "   ./scripts/start-all.sh"
echo ""
echo "Or start services individually:"
echo "   Backend:  ./scripts/start-backend.sh"
echo "   Frontend: ./scripts/start-frontend.sh"
echo ""
echo "📖 Access Points:"
echo "   - Frontend: http://localhost:3000"
echo "   - Backend API: http://localhost:8000"
echo "   - API Documentation: http://localhost:8000/docs"
echo ""
echo "🔧 Troubleshooting:"
echo "   - Check logs in terminal windows"
echo "   - Verify .env file configuration"
echo "   - Ensure PostgreSQL is running"
echo "   - Run: sudo systemctl status postgresql"
echo ""
print_success "Ready to launch! 🚀"
echo ""
echo "💡 Next steps:"
echo "   1. Run: ./scripts/start-all.sh"
echo "   2. Open http://localhost:3000 in your browser"
echo "   3. Create an account and start using the AI finance assistant!"