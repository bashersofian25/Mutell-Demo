import logging
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.middleware import AuditLogMiddleware

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer() if settings.DEBUG else structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(AuditLogMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.ALLOWED_ORIGINS.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.routers import (  # noqa: E402
    admin,
    aggregations,
    ai_configs,
    analytics,
    auth,
    dashboard,
    evaluations,
    notes,
    plans,
    reports,
    settings,
    slots,
    terminals,
    tenants,
    users,
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(slots.router, prefix="/api/v1/slots", tags=["Slots"])
app.include_router(evaluations.router, prefix="/api/v1/evaluations", tags=["Evaluations"])
app.include_router(aggregations.router, prefix="/api/v1/aggregations", tags=["Aggregations"])
app.include_router(terminals.router, prefix="/api/v1/terminals", tags=["Terminals"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(tenants.router, prefix="/api/v1/tenants", tags=["Tenants"])
app.include_router(notes.router, prefix="/api/v1/notes", tags=["Notes"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["Reports"])
app.include_router(plans.router, prefix="/api/v1/plans", tags=["Plans"])
app.include_router(ai_configs.router, prefix="/api/v1/settings/ai", tags=["AI Settings"])
app.include_router(settings.router, prefix="/api/v1/settings", tags=["Settings"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])


@app.get("/health")
async def health_check():
    return {"status": "ok"}
