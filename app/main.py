"""
BIRD Backend Main Application

FastAPI application setup with middleware, routes, and error handling.
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import logging
import logging.config

from config.settings import get_settings
from app.database import DatabaseManager
from app.routers import auth, workspaces, intelligence, vault, agents, campaigns

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()


# ============================================================================
# Lifespan Events
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    # Startup
    logger.info(f"Starting BIRD Backend - Environment: {settings.environment}")
    DatabaseManager.initialize()
    yield
    # Shutdown
    logger.info("Shutting down BIRD Backend")
    DatabaseManager.close()


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title=settings.app_name,
    description="Multi-Agent Intelligence System",
    version=settings.app_version,
    lifespan=lifespan
)


# ============================================================================
# CORS Middleware
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "details": exc.errors(),
            "status_code": 422
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "detail": str(exc) if settings.debug else "An error occurred",
            "status_code": 500
        }
    )


# ============================================================================
# Health Check Endpoints
# ============================================================================

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment
    }


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "api_v1": settings.api_v1_str,
        "api_v2": settings.api_v2_str
    }


# ============================================================================
# API Routes
# ============================================================================

# API v1 routes
app.include_router(
    auth.router,
    prefix=f"{settings.api_v1_str}/auth",
    tags=["Authentication"]
)

app.include_router(
    workspaces.router,
    prefix=f"{settings.api_v1_str}/workspaces",
    tags=["Workspaces"]
)

# API v2 routes (Multi-Agent System)
app.include_router(
    intelligence.router,
    prefix=f"{settings.api_v2_str}/intelligence",
    tags=["Intelligence"]
)

app.include_router(
    vault.router,
    prefix=f"{settings.api_v2_str}/vault",
    tags=["Vault"]
)

app.include_router(
    agents.router,
    prefix=f"{settings.api_v2_str}/agents",
    tags=["Agents"]
)

app.include_router(
    campaigns.router,
    prefix=f"{settings.api_v2_str}/campaigns",
    tags=["Campaigns"]
)


# ============================================================================
# Application Info
# ============================================================================

@app.get("/docs-info", tags=["Documentation"])
async def docs_info():
    """API documentation information."""
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "api_v1": f"{settings.api_v1_str}",
        "api_v2": f"{settings.api_v2_str}",
        "documentation": "/docs",
        "openapi_schema": "/openapi.json"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
