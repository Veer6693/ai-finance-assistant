#!/bin/bash

# Deploy to Vercel - Frontend
echo "🚀 Deploying AI Finance Assistant Frontend to Vercel..."

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI is not installed. Please install it first:"
    echo "   npm install -g vercel"
    exit 1
fi

# Navigate to frontend directory
cd "$(dirname "$0")/../frontend"

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Build the project to check for errors
echo "🔨 Building project..."
npm run build

# Deploy to Vercel
echo "🚀 Deploying to Vercel..."

# Set environment variables for production
vercel env add REACT_APP_API_URL production
echo "Enter your backend API URL (e.g., https://your-app.herokuapp.com/api/v1):"

vercel env add REACT_APP_ENVIRONMENT production
echo "production"

# Deploy
vercel --prod

echo "✅ Frontend deployment completed!"
echo ""
echo "🔧 Next steps:"
echo "1. Update your backend CORS settings to include the Vercel URL"
echo "2. Test the application end-to-end"
echo "3. Set up custom domain (optional)"
echo ""
echo "📱 Your app should be available at the URL shown above"