#!/bin/bash

# Deploy to Heroku - Backend
echo "🚀 Deploying AI Finance Assistant Backend to Heroku..."

# Check if Heroku CLI is installed
if ! command -v heroku &> /dev/null; then
    echo "❌ Heroku CLI is not installed. Please install it first:"
    echo "   https://devcenter.heroku.com/articles/heroku-cli"
    exit 1
fi

# Check if logged in to Heroku
if ! heroku auth:whoami &> /dev/null; then
    echo "❌ You are not logged in to Heroku. Please login first:"
    echo "   heroku login"
    exit 1
fi

# Set app name (change this to your preferred app name)
APP_NAME="ai-finance-assistant-backend"

# Check if app exists, create if it doesn't
if ! heroku apps:info $APP_NAME &> /dev/null; then
    echo "📦 Creating new Heroku app: $APP_NAME"
    heroku create $APP_NAME --region us
    
    # Add PostgreSQL addon
    echo "🗄️  Adding PostgreSQL addon..."
    heroku addons:create heroku-postgresql:essential-0 --app $APP_NAME
else
    echo "✅ App $APP_NAME already exists"
fi

# Set environment variables
echo "🔧 Setting environment variables..."
heroku config:set \
    SECRET_KEY=$(openssl rand -base64 32) \
    FRONTEND_URL="https://ai-finance-assistant-frontend.vercel.app" \
    RAZORPAY_API_KEY="rzp_test_mock_key" \
    RAZORPAY_API_SECRET="mock_secret_key" \
    ENVIRONMENT="production" \
    --app $APP_NAME

# Navigate to backend directory
cd "$(dirname "$0")/../backend"

# Initialize git if not already done
if [ ! -d ".git" ]; then
    echo "🔄 Initializing git repository..."
    git init
    git add .
    git commit -m "Initial commit"
fi

# Add Heroku remote
if ! git remote get-url heroku &> /dev/null; then
    echo "🔗 Adding Heroku remote..."
    heroku git:remote -a $APP_NAME
fi

# Deploy to Heroku
echo "🚀 Deploying to Heroku..."
git add .
git commit -m "Deploy to Heroku" --allow-empty
git push heroku main

# Run database migrations (if any)
echo "🗄️  Running database setup..."
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
print('Database tables created successfully!')
" --app $APP_NAME

# Show app info
echo "✅ Deployment completed!"
echo "📱 App URL: https://$APP_NAME.herokuapp.com"
echo "📊 Dashboard: https://dashboard.heroku.com/apps/$APP_NAME"
echo "📝 Logs: heroku logs --tail --app $APP_NAME"

echo ""
echo "🔧 Next steps:"
echo "1. Set up your database with sample data"
echo "2. Configure your frontend to use the Heroku backend URL"
echo "3. Test the API endpoints"
echo ""
echo "📖 API Documentation: https://$APP_NAME.herokuapp.com/docs"