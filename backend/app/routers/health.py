"""Health check router."""

from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["Health"])


@router.get("/health")
async def health_check():
    """Return service health status and OpenOA version."""
    try:
        import openoa
        openoa_version = openoa.__version__
    except ImportError:
        openoa_version = "not installed"

    return {
        "status": "healthy",
        "service": "OpenOA API",
        "openoa_version": openoa_version,
    }
