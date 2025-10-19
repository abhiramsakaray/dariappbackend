from fastapi import FastAPI, Depends, HTTPException, status, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer
from contextlib import asynccontextmanager
import asyncio
import os
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from datetime import datetime

from app.core.config import settings
from app.core.database import init_db
from app.api.v1 import auth, users, kyc, wallets, transactions, tokens, address_resolver, notifications, deposits, payment_methods, push_notifications

# Try to import price service, but handle if web3 dependencies are missing
try:
    from app.services.price_service import start_price_updater
    PRICE_SERVICE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Warning: Price service not available - {e}")
    print("💡 Install web3 dependencies later for full functionality")
    PRICE_SERVICE_AVAILABLE = False

security = HTTPBearer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    
    # Start background price updater only if available
    if PRICE_SERVICE_AVAILABLE and not settings.USE_TESTNET:
        asyncio.create_task(start_price_updater())
    
    yield
    
    # Shutdown
    pass

app = FastAPI(
    title="DARI Wallet V2 API",
    description="Semi-custodial crypto wallet system supporting USDC and USDT on Polygon",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for mobile app development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure this properly for production
)

# User cache clearing middleware - must be added after CORS
@app.middleware("http")
async def clear_user_cache_middleware(request: Request, call_next):
    """Clear user cache at the start of each request to prevent stale data"""
    from app.core.security import _current_user_cache
    _current_user_cache.set(None)
    response = await call_next(request)
    return response

# Create uploads directory if it doesn't exist
uploads_dir = "./uploads"
if not os.path.exists(uploads_dir):
    os.makedirs(uploads_dir)

# Mount static files for file serving
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include routers
# User-facing API routers only
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(kyc.router, prefix="/api/v1/kyc", tags=["KYC"])
app.include_router(wallets.router, prefix="/api/v1/wallets", tags=["Wallets"])
app.include_router(address_resolver.router, prefix="/api/v1/address", tags=["Address Resolver"])
app.include_router(transactions.router, prefix="/api/v1/transactions", tags=["Transactions"])
app.include_router(deposits.router, prefix="/api/v1/deposits", tags=["Deposits"])
app.include_router(tokens.router, prefix="/api/v1/tokens", tags=["Tokens"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["Notifications"])
app.include_router(payment_methods.router, prefix="/api/v1", tags=["Payment Methods"])
app.include_router(push_notifications.router, prefix="/api/v1", tags=["Push Notifications"])

# Root endpoints
@app.get("/")
async def root():
    return {
        "message": "DARI Wallet V2 API",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health"
    }

@app.get("/api/v1/")
async def root_v1():
    return {
        "message": "DARI Wallet V2 API",
        "version": "2.0.0",
        "status": "running",
        "prefix": "/api/v1",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/api/v1/health"
    }

# Health check endpoints
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0",
        "service": "DARI Wallet API"
    }

@app.get("/api/v1/health")
async def health_check_v1():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0",
        "service": "DARI Wallet API",
        "prefix": "/api/v1"
    }

# Additional utility endpoints
@app.get("/status")
async def status():
    return {
        "api": "DARI Wallet V2",
        "version": "2.0.0",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/v1/status")
async def status_v1():
    return {
        "api": "DARI Wallet V2",
        "version": "2.0.0",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "prefix": "/api/v1"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )