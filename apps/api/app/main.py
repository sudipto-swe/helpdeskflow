"""FastAPI Application entrypoint for HelpdeskFlow."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from apps.api.app.core.config import settings
from apps.api.app.core.logging import RequestIDMiddleware, logger
from apps.api.app.db.session import Base, engine

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="HelpdeskFlow API",
    description="RAG + Tool-Calling Agent for Support Ticket Workflow Automation",
    version="1.0.0"
)

app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    """Liveness probe: verifies process is alive."""
    return {"status": "ok", "service": "helpdeskflow-api"}


@app.get("/ready")
def readiness_check():
    """Readiness probe: verifies database connectivity and core subsystems."""
    db_status = "ok"
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(f"Readiness check database failure: {e}")
        db_status = f"unhealthy: {str(e)}"

    is_ready = db_status == "ok"
    return {
        "status": "ready" if is_ready else "not_ready",
        "database": db_status,
        "llm_provider": settings.LLM_PROVIDER,
        "environment": settings.ENVIRONMENT
    }
