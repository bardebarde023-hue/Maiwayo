import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from contextlib import asynccontextmanager

# Import modules directly (no app folder)
from database import init_db, get_db
from auth import router as auth_router
from user import router as user_router
from admin import router as admin_router
from tasks import router as tasks_router
from withdrawals import router as withdrawals_router

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
    print("\n⚠️ Server shutting down...")

# Initialize FastAPI app
app = FastAPI(
    title="Social Pay API",
    description="Complete earning app backend with task management and rewards",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(user_router, prefix="/api/user", tags=["User"])
app.include_router(admin_router, prefix="/api/admin", tags=["Admin"])
app.include_router(tasks_router, prefix="/api/tasks", tags=["Tasks"])
app.include_router(withdrawals_router, prefix="/api/withdrawals", tags=["Withdrawals"])

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
