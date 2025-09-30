from typing import Dict
from fastapi import APIRouter, HTTPException

home_route = APIRouter()


@home_route.get(
    "/",
    response_model=Dict[str, str],
    summary="Root endpoint",
    description="Returns a welcome message"
)


async def index() -> str:
    try:
        return {"message": "Welcome to Event Planner API"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@home_route.get(
    "/health",
    response_model=Dict[str, str],
    summary="Health check endpoint",
    description="Returns service health status"
)
async def health_check() -> Dict[str, str]:
    try:
        # Add actual health checks here
        return {"status": "healthy"}
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail="Service unavailable"
        )

@home_route.get('/test')
async def test():
    return {"message": "success"}