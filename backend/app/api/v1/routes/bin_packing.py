from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.stock_label import StockLabel
from app.repositories.truck_repository import TruckRepository
from app.schemas.bin_packing import LabelInput, PackingFilters, TruckInput
from app.services.bin_packing_service import BinPackingService

router = APIRouter(prefix="/bin-packing", tags=["bin-packing"])


class PackRequest(BaseModel):
    truck_id: str
    filters: PackingFilters = PackingFilters()
    max_iterations: int | None = None


class LoadPlanItemOut(BaseModel):
    progressivo: str
    volume_tons: float


class LoadPlanOut(BaseModel):
    items: list[LoadPlanItemOut]
    total_weight_tons: float
    partial: bool


@router.post("/pack", response_model=LoadPlanOut)
async def pack(body: PackRequest, session: AsyncSession = Depends(get_session)):
    truck_orm = await TruckRepository(session).get_by_id(body.truck_id)
    if not truck_orm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Truck not found")

    result = await session.execute(select(StockLabel))
    labels_orm = result.scalars().all()

    labels = [
        LabelInput(
            progressivo=lbl.progressivo,
            volume_tons=float(lbl.volume_tons),
            market_type=lbl.market_type,
            country=lbl.country or "",
            order_condition=lbl.order_condition or "",
            exit_date=date.fromisoformat(lbl.exit_date) if lbl.exit_date else None,
        )
        for lbl in labels_orm
    ]

    truck = TruckInput(id=truck_orm.id, max_weight_tons=float(truck_orm.max_weight_tons))
    plan = BinPackingService.pack(labels, truck, body.filters, body.max_iterations)

    return LoadPlanOut(
        items=[LoadPlanItemOut(progressivo=i.progressivo, volume_tons=i.volume_tons) for i in plan.items],
        total_weight_tons=plan.total_weight_tons,
        partial=plan.partial,
    )
