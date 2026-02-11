import os
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
import uvicorn
from contextlib import asynccontextmanager

# Import app modules
from app.database import init_db, get_db
from app.auth import router as auth_router
from app.user import router as user_router
from app.admin import router as admin_router
from app.tasks import router as tasks_router
from app.withdrawals import router as withdrawals_router
from app.support import router as support_router

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    print("=" * 60)
    print("🤖 SOCIAL PAY API SERVER")
    print("=" * 60)
    print("✅ Database initialized")
    print("✅ All routes registered")
    print("=" * 60)
    yield
    print("\n⚠️  Server shutting down...")

# Initialize app
app = FastAPI(
    title="Social Pay API",
    description="Complete earning app backend with task management and rewards",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(user_router, prefix="/api/user", tags=["User"])
app.include_router(admin_router, prefix="/api/admin", tags=["Admin"])
app.include_router(tasks_router, prefix="/api/tasks", tags=["Tasks"])
app.include_router(withdrawals_router, prefix="/api/withdrawals", tags=["Withdrawals"])
app.include_router(support_router, prefix="/api/support", tags=["Support"])

@app.get("/")
async def root():
    return {
        "message": "Welcome to Social Pay API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Run Uvicorn
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
        reload=True
    )