"""
main.py — FastAPI application entry point for PharmaAgent AI Backend.

Phase 3 additions:
  - Voice Agent router (STT transcript → pharmacy agent → TTS)
  - Symptom Checker router (MCQ triage + red-flag detection)
  - Webhook Fulfillment router (simulate + retrigger + history)
  - Analytics router (KPI queries for admin dashboard)
  - Settings router (user theme + language persistence)

Run with:
    uvicorn app.main:app --reload --port 8000
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import logging
import os

from app.config import settings
from app.database import init_db, SessionLocal
from app.routes import auth, medicines, orders, agent, payment

# Phase 2 routers
from app.routes import prescriptions, pharmacist, refill_alerts

# Phase 3 routers
from app.routes import voice_routes, symptom_routes, webhook_routes, analytics_routes, settings_routes, admin_users

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Application Lifespan Manager
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application startup and shutdown events.

    On startup:
    - Initialize database tables (create if not exist)
    - Seed medicine inventory with sample data
    - Create default admin user

    On shutdown:
    - Clean up resources (if needed)
    """
    # STARTUP
    logger.info("🚀 PharmaAgent AI Backend starting up...")

    # Initialize DB tables
    init_db()

    # Seed initial data
    from app.utils.seed_data import seed_medicines, seed_admin_user, seed_pharmacist_user, seed_demo_user
    db = SessionLocal()
    try:
        seed_medicines(db)
        seed_admin_user(db)
        seed_pharmacist_user(db)  # Phase 2: adds pharmacist account
    finally:
        db.close()

    # Files are now securely uploaded to Supabase Storage, bypassing local saves.
    logger.info("Cloud storage configuration initialized.")

    logger.info("✅ Backend ready. API docs available at http://localhost:8000/docs")

    yield  # Application runs here

    # SHUTDOWN
    logger.info("🛑 PharmaAgent AI Backend shutting down...")


# ---------------------------------------------------------------------------
# FastAPI Application Instance
# ---------------------------------------------------------------------------
app = FastAPI(
    title="PharmaAgent AI — Backend API",
    description=(
        "Autonomous pharmacy system powered by LangChain + Gemini 2.0 Flash. "
        "Phase 2: Vision Agent (prescription scanning), Refill Prediction Agent, "
        "Pharmacist verification workflow, expiry enforcement, multi-agent coordination."
    ),
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",       # Swagger UI
    redoc_url="/redoc",     # ReDoc UI
)


# ---------------------------------------------------------------------------
# Exception Handlers
# ---------------------------------------------------------------------------
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request: Request, exc: RequestValidationError):
    """Return user-friendly message for request validation errors (e.g. malformed JSON body)."""
    errors = exc.errors()
    first_msg = errors[0]["msg"] if errors else "Invalid request"
    return JSONResponse(
        status_code=422,
        content={"detail": first_msg},
    )


# ---------------------------------------------------------------------------
# CORS Middleware
# ---------------------------------------------------------------------------
# Allows the Next.js frontend (localhost:3000) to make API requests.
# In production, replace with your actual domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Register Routers
# ---------------------------------------------------------------------------
app.include_router(auth.router)              # /auth/register, /auth/login
app.include_router(medicines.router)         # /medicines, /medicines/search, /medicines/{id}
app.include_router(orders.router)            # /orders/create, /orders/user/{id}, /orders/all
app.include_router(agent.router)             # /agent/chat
app.include_router(payment.router)           # /payment/process

# Phase 2 routers
app.include_router(prescriptions.router)     # /prescriptions/upload, /prescriptions/user/{id}
app.include_router(pharmacist.router)        # /pharmacist/prescriptions/pending, /verify
app.include_router(refill_alerts.router)     # /refill-alerts/user/{id}, /run-prediction

# Phase 3 routers
app.include_router(voice_routes.router)      # /agent/voice-message, /agent/languages
app.include_router(symptom_routes.router)    # /symptom/check, /symptom/continue
app.include_router(webhook_routes.router)    # /webhook/simulate, /retrigger/{id}, /events/{id}
app.include_router(analytics_routes.router)  # /analytics/overview, /medicines, /refills, /fulfillment
app.include_router(settings_routes.router)   # /settings/preferences
app.include_router(admin_users.router)       # /admin/pharmacists/pending, /admin/pharmacists/approve


# ---------------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------------
@app.get("/health", tags=["System"])
async def health_check():
    """
    Health check endpoint.

    Returns system status and version information.
    Used by deployment platforms to verify the service is running.
    """
    return {
        "status": "healthy",
        "service": "PharmaAgent AI Backend",
        "version": "3.0.0",
        "phase": "Phase 3 — Voice, Symptom Checker, Analytics, Webhooks",
        "langsmith_project": settings.langchain_project,
    }



@app.get("/", tags=["System"])
async def root():
    """Root endpoint — redirects users to API documentation."""
    return {
        "message": "Welcome to PharmaAgent AI Backend API",
        "docs": "http://localhost:8000/docs",
        "health": "http://localhost:8000/health",
    }
