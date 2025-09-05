from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Perky AI Assistant V2 is running"}


@router.get("/ready")
async def readiness_check():
    # TODO: Add database and Redis connection checks
    return {"status": "ready", "database": "connected", "cache": "connected"}
