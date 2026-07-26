from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from backend.config.logging import configure_logging, get_logger
from backend.config.settings import settings, assert_secret_key_is_safe
from backend.api.routers.auth import router as auth_router
from backend.database.init_db import init_db
from backend.database.session import SessionLocal
from backend.service.marketplace_service import MarketplaceService
from backend.api.routers.marketplace import (
    router as marketplace_router
)
from backend.api.routers.chat import (
    router as chat_router
)
from backend.api.routers.dashboard import (
    router as dashboard_router
)
from backend.api.routers.inventory import (
    router as inventory_router
)
from backend.api.routers.orders import (
    router as orders_router
)
from backend.api.routers.analytics import (
    router as analytics_router
)

configure_logging()
logger = get_logger(__name__)

# Create FastAPI application
app = FastAPI(
    title="SellerOS API",
    version="1.0.0",
    description="Backend API for SellerOS",
)

# Without this, every request the React frontend makes from its own
# origin (a different port during dev, a different domain in prod)
# gets blocked by the browser before it even reaches these routes —
# regardless of how correct the API itself is. allow_credentials=True
# because the auth flow uses a Bearer token header, not cookies, but
# some frontend HTTP clients still send credentials by default.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Create database tables on startup
@app.on_event("startup")
def startup_event():
    assert_secret_key_is_safe(settings)

    init_db()

    # session_store (inside backend/ai/) is an in-process registry —
    # it starts empty on every restart even though marketplace_accounts
    # still has every previously-connected account. Without this, a
    # seller's "connected" marketplace would silently stop working for
    # chat/dashboard queries after any redeploy or crash recovery, while
    # GET /marketplaces kept reporting it as connected.
    db = SessionLocal()
    try:
        restored = MarketplaceService.restore_all_sessions(db)
        logger.info("Restored %d marketplace session(s) into session_store.", restored)
    finally:
        db.close()


# Liveness check — "is the process up at all". Deliberately does not
# touch the DB, so a slow/unavailable DB shows up as a /health/ready
# failure, not a /health failure; load balancers and orchestrators
# typically use this one to decide whether to restart the container.
@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "SellerOS API",
    }


# Readiness check — "is the process able to actually serve requests
# right now". Runs a trivial query so a DB that's down, mid-migration,
# or unreachable is caught here rather than surfacing as a confusing
# 500 on the first real request that touches it. Orchestrators (k8s
# readiness probes, load balancers) should point here, not at /health,
# when deciding whether to route traffic to this instance.
@app.get("/health/ready")
def readiness():
    try:
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
        finally:
            db.close()
    except Exception as e:
        logger.error("Readiness check failed: %s", e)
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "service": "SellerOS API", "detail": str(e)},
        )

    return {
        "status": "ready",
        "service": "SellerOS API",
    }


# Register routers
app.include_router(auth_router)
app.include_router(
    marketplace_router
)
app.include_router(chat_router)
app.include_router(
    dashboard_router
)
app.include_router(
    inventory_router
)
app.include_router(
    orders_router
)
app.include_router(
    analytics_router
)