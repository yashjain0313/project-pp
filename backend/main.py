"""
CareSync — Patient Care Gap Analysis & Risk Stratification Platform
Main FastAPI Application Entry Point
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import engine, SessionLocal, Base
from models import User  # Import all models to register them
import models  # Ensure all models are loaded
from auth import router as auth_router
from routers.patients import router as patients_router
from routers.care_gaps import router as care_gaps_router
from routers.care_plans import router as care_plans_router
from routers.analytics import router as analytics_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    # Create all database tables
    Base.metadata.create_all(bind=engine)
    print("📦 Database tables created")

    # Seed data on first run
    db = SessionLocal()
    try:
        from seed_data import seed_database
        seed_database(db)
    except Exception as e:
        print(f"⚠️  Seeding error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

    yield  # Application runs

    print("👋 CareSync shutting down")


# ─── App Setup ──────────────────────────────────────────

app = FastAPI(
    title="CareSync API",
    description=(
        "Patient Care Gap Analysis & Risk Stratification Platform. "
        "Identifies missing preventive care, stratifies patient risk, "
        "and provides actionable insights for care coordinators."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Register Routers ──────────────────────────────────

app.include_router(auth_router)
app.include_router(patients_router)
app.include_router(care_gaps_router)
app.include_router(care_plans_router)
app.include_router(analytics_router)


# ─── Root Endpoint ──────────────────────────────────────

@app.get("/")
async def root():
    return {
        "name": "CareSync API",
        "version": "1.0.0",
        "description": "Patient Care Gap Analysis & Risk Stratification Platform",
        "docs": "/docs",
        "status": "healthy"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
