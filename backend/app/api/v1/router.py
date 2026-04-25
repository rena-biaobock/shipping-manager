from fastapi import APIRouter

from app.api.v1.routes.locations import router as locations_router
from app.api.v1.routes.trucks import router as trucks_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(locations_router)
api_router.include_router(trucks_router)
