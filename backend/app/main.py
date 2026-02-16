"""
OpenOA API — FastAPI application wrapping the OpenOA wind plant analysis library.

This API exposes OpenOA's operational analysis methods as REST endpoints,
allowing users to upload wind plant data and run analyses like AEP estimation,
electrical losses computation, wake losses analysis, and more.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import analysis, data, health

# ──────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Lifespan (replaces deprecated on_event)
# ──────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic."""
    try:
        import openoa
        logger.info(f"OpenOA API started — OpenOA version {openoa.__version__}")
    except ImportError:
        logger.warning("OpenOA is NOT installed — analysis endpoints will fail")
    logger.info("API docs available at /docs")
    yield
    logger.info("OpenOA API shutting down")


# ──────────────────────────────────────────────
# App
# ──────────────────────────────────────────────

app = FastAPI(
    title="OpenOA API",
    description=(
        "REST API wrapping the **OpenOA** wind plant operational analysis library. "
        "Upload SCADA, meter, and reanalysis data, then run analyses such as "
        "Monte Carlo AEP estimation, electrical losses, wake losses, and turbine energy."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ──────────────────────────────────────────────
# CORS (allow all origins for development)
# ──────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────────────────────────────────────────────
# Routers
# ──────────────────────────────────────────────

app.include_router(health.router)
app.include_router(data.router)
app.include_router(analysis.router)


# ──────────────────────────────────────────────
# Root redirect
# ──────────────────────────────────────────────

@app.get("/", include_in_schema=False)
async def root():
    """Redirect root to API docs."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/docs")
