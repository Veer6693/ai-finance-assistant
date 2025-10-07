# 🚀 Setup Guide for AI-Powered Personal Finance Assistant

This guide will help you set up the AI-Powered Personal Finance Assistant on a new system from scratch.

## ⚡ **Quick Start (TL;DR)**

```bash
git clone https://github.com/Veer6693/ai-finance-assistant.git
cd ai-finance-assistant
chmod +x scripts/*.sh
./scripts/setup.sh
./scripts/start-all.sh
```

**Done!** 🎉 Open http://localhost:3000 and login with `test@example.com` / `password123`

---

## ✅ Files Successfully Pushed to GitHub

**All essential files have been pushed to the repository including:**

### Backend Files ✅
- `backend/main.py` - Main FastAPI application
- `backend/requirements.txt` - Python dependencies
- `backend/.env.example` - Environment configuration template
- `backend/app/` - All application modules (models, routes, services, AI modules)
- `backend/tests/` - Test suite

### Frontend Files ✅
- `frontend/src/` - Complete React application
- `frontend/package.json` - Node.js dependencies
- `frontend/public/` - Static assets
- All React components, services, and utilities

### Configuration Files ✅
- `README.md` - Comprehensive documentation
- `docker-compose.yml` - Docker deployment
- `.gitignore` - Proper exclusions
- `scripts/` - Startup and deployment scripts
- `.github/workflows/` - CI/CD pipeline

### Documentation ✅
- `CONTRIBUTING.md` - Contribution guidelines
- `LICENSE` - MIT license
- `PROJECT_SUMMARY.md` - Project overview

## 📋 Prerequisites

Before setting up the project, ensure you have:

- **Python 3.8+** (Check: `python --version`)
- **Node.js 14+** (Check: `node --version`)
- **npm or yarn** (Check: `npm --version`)
- **Git** (Check: `git --version`)

## 🛠️ Complete Setup Commands for New System

### Option 1: 🚀 **Quick Script-Based Setup (Recommended)**

The easiest way to set up the project is using our automated setup scripts:

```bash
# Clone the repository
git clone https://github.com/Veer6693/ai-finance-assistant.git
cd ai-finance-assistant

# Make scripts executable
chmod +x scripts/*.sh

# Run complete setup (installs all dependencies)
./scripts/setup.sh

# Start both backend and frontend servers
./scripts/start-all.sh
```

**That's it! 🎉** The scripts will:
- ✅ Create Python virtual environment
- ✅ Install all Python dependencies
- ✅ Install all Node.js dependencies
- ✅ Set up environment configuration
- ✅ Initialize the database
- ✅ Start both servers with proper configuration

### **Setup Method Comparison**

| Method | Commands | Time | Error Handling | Recommended For |
|--------|----------|------|----------------|-----------------|
| **🚀 Scripts** | 4 commands | ~2-3 min | ✅ Automatic | **Everyone** |
| 📋 Manual | 10+ commands | ~5-10 min | ⚠️ Manual | Learning/Understanding |
| 🐳 Docker | 2 commands | ~3-5 min | ✅ Containerized | Production/Isolation |

### Option 2: 📋 **Manual Step-by-Step Setup**

### 1. Clone the Repository

```bash
# Clone the repository
git clone https://github.com/Veer6693/ai-finance-assistant.git
cd ai-finance-assistant
```

### 2. Backend Setup

```bash
# Create and activate virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Navigate to backend directory
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env file with your configurations (optional for development)

# Initialize database (will create SQLite database)
# Database will be automatically created when you start the server

# Start the backend server
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend Setup (New Terminal)

```bash
# Navigate to frontend directory
cd ai-finance-assistant/frontend

# Install Node.js dependencies
npm install

# Start the development server
npm start
```

### 4. Verify Setup

After running both commands, you should have:

- **Backend API**: Running on http://localhost:8000
- **Frontend App**: Running on http://localhost:3000
- **API Documentation**: Available at http://localhost:8000/docs

### 5. Test the Application

**Use the default test account:**
- Email: `test@example.com`
- Password: `password123`

Or create a new account using the registration form.

## 🐳 Alternative: Docker Setup

If you prefer using Docker:

```bash
# Clone the repository
git clone https://github.com/Veer6693/ai-finance-assistant.git
cd ai-finance-assistant

# Build and run with Docker Compose
docker-compose up --build
```

This will automatically set up both backend and frontend with all dependencies.

## 📜 **Available Setup Scripts**

The repository includes several helpful scripts in the `scripts/` directory:

### **Setup Scripts**
```bash
# Complete project setup (one-time)
./scripts/setup.sh                # Full setup with all dependencies

# Individual component setup
./scripts/setup-backend.sh         # Backend only setup
./scripts/setup-frontend.sh        # Frontend only setup
```

### **Start Scripts**
```bash
# Start both backend and frontend
./scripts/start-all.sh            # Starts both servers simultaneously

# Start individual components
./scripts/start-backend.sh        # Backend server only (port 8000)
./scripts/start-frontend.sh       # Frontend server only (port 3000)
```

### **Deployment Scripts**
```bash
# Deploy to production
./scripts/deploy-all.sh           # Deploy both backend and frontend
./scripts/deploy-backend.sh       # Deploy backend only
./scripts/deploy-frontend.sh      # Deploy frontend only
```

### **Script Features**
- ✅ **Automatic dependency detection** and installation
- ✅ **Error handling** and validation
- ✅ **Colored output** for better readability
- ✅ **Progress indicators** and status messages
- ✅ **Cleanup functions** for graceful shutdown
- ✅ **Cross-platform compatibility** (Linux/Mac/WSL)

## 🔧 Development Environment

### Backend Development
```bash
# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate    # Windows

# Navigate to backend
cd backend

# Run with auto-reload
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest

# Check API documentation
# Visit: http://localhost:8000/docs
```

### Frontend Development
```bash
# Navigate to frontend
cd frontend

# Start development server
npm start

# Run tests
npm test

# Build for production
npm run build
```

## 📁 Project Structure After Setup

```
ai-finance-assistant/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── ai_modules/        # AI/ML components
│   │   ├── models/            # Database models
│   │   ├── routes/            # API endpoints
│   │   ├── services/          # Business logic
│   │   └── utils/             # Helper functions
│   ├── main.py                # FastAPI application
│   ├── requirements.txt       # Python dependencies
│   └── .env                   # Environment variables (created from .env.example)
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── services/          # API services
│   │   └── utils/             # Helper functions
│   ├── public/                # Static assets
│   ├── package.json           # Node.js dependencies
│   └── node_modules/          # Installed packages (after npm install)
├── venv/                      # Python virtual environment (created)
├── finance_assistant.db      # SQLite database (auto-created)
└── README.md                  # Documentation
```

## 🚨 Troubleshooting

### Common Issues and Solutions

**1. Port Already in Use**
```bash
# Kill processes on ports 8000 or 3000
sudo lsof -ti:8000 | xargs kill -9
sudo lsof -ti:3000 | xargs kill -9
```

**2. Python Dependencies Issues**
```bash
# Upgrade pip
pip install --upgrade pip

# Install specific versions
pip install -r requirements.txt --force-reinstall
```

**3. Node Dependencies Issues**
```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

**4. Database Issues**
```bash
# Delete and recreate database
rm backend/finance_assistant.db
# Restart backend server to auto-create new database
```

**5. CORS Issues**
- Ensure backend is running on port 8000
- Check that frontend is configured to use http://localhost:8000

## ✅ Success Indicators

You'll know the setup is successful when:

1. ✅ Backend starts without errors and shows:
   ```
   ✅ Auth routes loaded
   ✅ Transaction routes loaded
   ✅ Analysis routes loaded
   ✅ AI query routes loaded
   ✅ UPI routes loaded
   ✅ Database initialized successfully
   ```

2. ✅ Frontend compiles successfully:
   ```
   Compiled successfully!
   You can now view ai-finance-assistant-frontend in the browser.
   Local: http://localhost:3000
   ```

3. ✅ You can access:
   - Frontend app at http://localhost:3000
   - API documentation at http://localhost:8000/docs
   - Health endpoint returns 200 OK: http://localhost:8000/health

4. ✅ You can log in with test@example.com / password123

## 🎯 Next Steps After Setup

1. **Explore the Application**
   - Test user registration and login
   - Add sample transactions
   - Try the AI chat feature
   - Create budgets and view analytics

2. **Development**
   - Check out the API documentation
   - Explore the codebase
   - Run the test suite
   - Try making changes and see hot reload

3. **Deployment**
   - Use the provided Docker configuration
   - Deploy to cloud platforms using included scripts
   - Configure production environment variables

## 📞 Support

If you encounter any issues:
1. Check this troubleshooting guide
2. Review the main README.md
3. Check the GitHub issues
4. Ensure all prerequisites are installed correctly

---

**Happy coding! 🚀**