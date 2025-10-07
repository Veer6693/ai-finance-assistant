from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# FastAPI app initialization
app = FastAPI(
    title="AI Finance Assistant API",
    description="API for AI-Powered Personal Finance Assistant with UPI Integration",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "AI-Powered Personal Finance Assistant API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "API is running"}

# Simple test auth endpoint
@app.post("/api/v1/auth/login")
async def test_login():
    return {
        "access_token": "test_token",
        "token_type": "bearer",
        "user": {
            "id": 1,
            "email": "test@example.com",
            "name": "Test User"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main_test_cors:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )