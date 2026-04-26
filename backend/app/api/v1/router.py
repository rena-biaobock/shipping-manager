from fastapi import APIRouter

from app.api.v1.routes.bin_packing import router as bin_packing_router
from app.api.v1.routes.locations import router as locations_router
from app.api.v1.routes.shipments import router as shipments_router
from app.api.v1.routes.stock_labels import router as stock_labels_router
from app.api.v1.routes.trucks import router as trucks_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(locations_router)
api_router.include_router(trucks_router)
api_router.include_router(stock_labels_router)
api_router.include_router(shipments_router)
api_router.include_router(bin_packing_router)
