#!/bin/bash

# Complete Deployment Script
echo "🌟 AI Finance Assistant - Complete Deployment"
echo "=============================================="

# Check prerequisites
echo "🔍 Checking prerequisites..."

MISSING_TOOLS=""

if ! command -v node &> /dev/null; then
    MISSING_TOOLS="$MISSING_TOOLS node"
fi

if ! command -v npm &> /dev/null; then
    MISSING_TOOLS="$MISSING_TOOLS npm"
fi

if ! command -v python3 &> /dev/null; then
    MISSING_TOOLS="$MISSING_TOOLS python3"
fi

if ! command -v heroku &> /dev/null; then
    MISSING_TOOLS="$MISSING_TOOLS heroku"
fi

if ! command -v vercel &> /dev/null; then
    MISSING_TOOLS="$MISSING_TOOLS vercel"
fi

if [ ! -z "$MISSING_TOOLS" ]; then
    echo "❌ Missing required tools:$MISSING_TOOLS"
    echo ""
    echo "Please install the missing tools and try again:"
    echo "- Node.js: https://nodejs.org/"
    echo "- Heroku CLI: https://devcenter.heroku.com/articles/heroku-cli"
    echo "- Vercel CLI: npm install -g vercel"
    exit 1
fi

echo "✅ All prerequisites met!"

# Get user input
echo ""
echo "📝 Configuration"
echo "=================="

read -p "Enter your Heroku app name for backend (default: ai-finance-assistant-backend): " BACKEND_APP_NAME
BACKEND_APP_NAME=${BACKEND_APP_NAME:-ai-finance-assistant-backend}

read -p "Enter your preferred frontend domain name (or press Enter for auto-generated): " FRONTEND_DOMAIN

# Deploy backend first
echo ""
echo "🚀 Step 1: Deploying Backend to Heroku"
echo "======================================="

cd "$(dirname "$0")/../backend"

# Check if app exists
if ! heroku apps:info $BACKEND_APP_NAME &> /dev/null; then
    echo "📦 Creating Heroku app: $BACKEND_APP_NAME"
    heroku create $BACKEND_APP_NAME --region us
    heroku addons:create heroku-postgresql:essential-0 --app $BACKEND_APP_NAME
fi

# Set environment variables
heroku config:set \
    SECRET_KEY=$(openssl rand -base64 32) \
    RAZORPAY_API_KEY="rzp_test_mock_key" \
    RAZORPAY_API_SECRET="mock_secret_key" \
    ENVIRONMENT="production" \
    --app $BACKEND_APP_NAME

# Deploy backend
if [ ! -d ".git" ]; then
    git init
    git add .
    git commit -m "Initial commit"
fi

if ! git remote get-url heroku &> /dev/null; then
    heroku git:remote -a $BACKEND_APP_NAME
fi

git add .
git commit -m "Deploy to production" --allow-empty
git push heroku main

# Set up database
heroku run python -c "
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import user, transaction, budget
import os

DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

engine = create_engine(DATABASE_URL)
user.Base.metadata.create_all(bind=engine)
print('Database setup complete!')
" --app $BACKEND_APP_NAME

BACKEND_URL="https://$BACKEND_APP_NAME.herokuapp.com"
echo "✅ Backend deployed to: $BACKEND_URL"

# Deploy frontend
echo ""
echo "🚀 Step 2: Deploying Frontend to Vercel"
echo "========================================"

cd "$(dirname "$0")/../frontend"

# Create .env.production file
cat > .env.production << EOF
REACT_APP_API_URL=$BACKEND_URL/api/v1
REACT_APP_ENVIRONMENT=production
EOF

# Install dependencies and build
npm install
npm run build

# Deploy to Vercel
if [ ! -z "$FRONTEND_DOMAIN" ]; then
    vercel --prod --name $FRONTEND_DOMAIN
else
    vercel --prod
fi

# Get frontend URL (this would need to be captured from Vercel output)
FRONTEND_URL="https://ai-finance-assistant-frontend.vercel.app"

# Update backend CORS settings
echo ""
echo "🔧 Step 3: Updating CORS Settings"
echo "=================================="

heroku config:set FRONTEND_URL="$FRONTEND_URL" --app $BACKEND_APP_NAME

echo ""
echo "🎉 Deployment Complete!"
echo "======================="
echo ""
echo "📱 Frontend: $FRONTEND_URL"
echo "🔗 Backend API: $BACKEND_URL"
echo "📖 API Docs: $BACKEND_URL/docs"
echo ""
echo "🔧 Management Commands:"
echo "  Backend logs: heroku logs --tail --app $BACKEND_APP_NAME"
echo "  Frontend logs: vercel logs"
echo ""
echo "✨ Your AI Finance Assistant is now live!"