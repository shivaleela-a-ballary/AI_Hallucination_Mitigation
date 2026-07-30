"""
Main entry point for the AI Hallucination Mitigation Backend.
"""
from api.utils.logger import logger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.chat import router as chat_router
from api.routes.health import router as health_router
from api.routes.history import router as history_router

from api.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API for Retrieval-Augmented Generation and Verification",
    version=settings.APP_VERSION,
)
# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # Change this later to your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(chat_router, prefix="/api")
app.include_router(health_router, prefix="/api")
app.include_router(history_router, prefix="/api")


@app.get("/")
def root():
    return {
        "message": "Welcome to AI Hallucination Mitigation API",
        "status": "running"
    }