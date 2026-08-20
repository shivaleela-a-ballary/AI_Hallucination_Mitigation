"""
Main entry point for the AI Hallucination Mitigation Backend.
"""
from contextlib import asynccontextmanager

from api.utils.logger import logger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.auth import router as auth_router
from api.routes.user import router as user_router
from api.routes.chat import router as chat_router
from api.routes.health import router as health_router
from api.routes.history import router as history_router
from api.routes.verify import router as verify_router

from api.config import settings
from api.db.mongodb import db_manager
from api.middleware.error_handler import register_error_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing database connections...")
    db_manager.connect()
    yield
    # Shutdown
    logger.info("Closing database connections...")
    db_manager.close()


app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API for Retrieval-Augmented Generation, Verification, and Authentication",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=r"^https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
register_error_handlers(app)

# Register API routes
app.include_router(auth_router, prefix="/api")
app.include_router(user_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(health_router, prefix="/api")
app.include_router(history_router, prefix="/api")
app.include_router(verify_router, prefix="/api")


@app.get("/")
def root():
    return {
        "message": "Welcome to AI Hallucination Mitigation API",
        "status": "running",
        "version": settings.APP_VERSION,
    }

