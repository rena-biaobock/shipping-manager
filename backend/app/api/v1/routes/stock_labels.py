from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.repositories.label_location_history_repository import LabelLocationHistoryRepository
from app.repositories.location_repository import LocationRepository
from app.repositories.stock_label_repository import StockLabelRepository
from app.schemas.stock_label import StockLabelLocationUpdate, StockLabelRead, StockLabelStatusUpdate
from app.services.label_status_service import InvalidTransitionError, LabelStatusService

router = APIRouter(prefix="/stock-labels", tags=["stock-labels"])


@router.get("", response_model=list[StockLabelRead])
async def list_stock_labels(
    status: str | None = Query(default=None),
    market_type: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
):
    repo = StockLabelRepository(session)
    if status is not None:
        return await repo.list_by_status(status)
    if market_type is not None:
        return await repo.list_by_market_type(market_type)
    from sqlalchemy import select
    from app.models.stock_label import StockLabel
    result = await session.execute(select(StockLabel))
    return list(result.scalars().all())


@router.get("/{progressivo}", response_model=StockLabelRead)
async def get_stock_label(progressivo: str, session: AsyncSession = Depends(get_session)):
    label = await StockLabelRepository(session).get_by_progressivo(progressivo)
    if not label:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Label not found")
    return label


@router.patch("/{progressivo}/status", response_model=StockLabelRead)
async def update_stock_label_status(
    progressivo: str,
    body: StockLabelStatusUpdate,
    session: AsyncSession = Depends(get_session),
):
    repo = StockLabelRepository(session)
    label = await repo.get_by_progressivo(progressivo)
    if not label:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Label not found")
    try:
        LabelStatusService.transition(label.status, body.new_status)
    except InvalidTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return await repo.update_status(progressivo, body.new_status)


@router.patch("/{progressivo}/location", response_model=StockLabelRead)
async def update_stock_label_location(
    progressivo: str,
    body: StockLabelLocationUpdate,
    session: AsyncSession = Depends(get_session),
):
    repo = StockLabelRepository(session)
    label = await repo.get_by_progressivo(progressivo)
    if not label:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Label not found")

    location = await LocationRepository(session).get_by_id(body.location_id)
    if not location:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")

    await LabelLocationHistoryRepository(session).record(
        progressivo=progressivo,
        to_location_id=body.location_id,
        from_location_id=label.location_id,
    )
    return await repo.update_location(progressivo, body.location_id)
