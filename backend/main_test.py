from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# FastAPI app initialization
app = FastAPI(
    title="AI Finance Assistant API",
    description="API for AI-Powered Personal Finance Assistant with UPI Integration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database tables on application startup."""
    try:
        init_db()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"⚠️ Database initialization error: {e}")

@app.get("/")
async def root():
    return {
        "message": "AI-Powered Personal Finance Assistant API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "API is running"}

# Try to import routes individually to isolate issues
try:
    from app.routes import auth
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
    print("✅ Auth routes loaded")
except Exception as e:
    print(f"❌ Auth routes failed: {e}")

try:
    from app.routes import transactions
    app.include_router(transactions.router, prefix="/api/v1/transactions", tags=["transactions"])
    print("✅ Transaction routes loaded")
except Exception as e:
    print(f"❌ Transaction routes failed: {e}")

try:
    from app.routes import analysis
    app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["analysis"])
    print("✅ Analysis routes loaded")
except Exception as e:
    print(f"❌ Analysis routes failed: {e}")

try:
    from app.routes import ai_query
    app.include_router(ai_query.router, prefix="/api/v1/ai", tags=["ai-queries"])
    print("✅ AI query routes loaded")
except Exception as e:
    print(f"❌ AI query routes failed: {e}")

try:
    from app.routes import upi
    app.include_router(upi.router, prefix="/api/v1/upi", tags=["upi-integration"])
    print("✅ UPI routes loaded")
except Exception as e:
    print(f"❌ UPI routes failed: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main_test:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )