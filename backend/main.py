from fastapi import FastAPI

from backend.api.routers.auth import router as auth_router
from backend.database.init_db import init_db
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

# Create FastAPI application
app = FastAPI(
    title="SellerOS API",
    version="1.0.0",
    description="Backend API for SellerOS",
)


# Create database tables on startup
@app.on_event("startup")
def startup_event():
    init_db()


# Health check
@app.get("/health")
def health():
    return {
        "status": "healthy",
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