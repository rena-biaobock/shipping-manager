from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.load_item import LoadItem
from app.models.shipment import Shipment
from app.repositories.load_item_repository import LoadItemRepository
from app.repositories.shipment_repository import ShipmentRepository
from app.repositories.truck_repository import TruckRepository
from app.schemas.shipment import (
    LoadItemRead,
    ShipmentCreate,
    ShipmentLabelsAdd,
    ShipmentRead,
    ShipmentStatusUpdate,
)
from app.services.shipment_status_service import InvalidShipmentTransitionError, ShipmentStatusService

router = APIRouter(prefix="/shipments", tags=["shipments"])


@router.get("", response_model=list[ShipmentRead])
async def list_shipments(
    status: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
):
    if status is not None:
        return await ShipmentRepository(session).list_by_status(status)
    result = await session.execute(select(Shipment))
    return list(result.scalars().all())


@router.post("", response_model=ShipmentRead, status_code=status.HTTP_201_CREATED)
async def create_shipment(body: ShipmentCreate, session: AsyncSession = Depends(get_session)):
    truck = await TruckRepository(session).get_by_id(body.truck_id)
    if not truck:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Truck not found")
    shipment = Shipment(
        truck_id=body.truck_id,
        destination=body.destination,
        customer=body.customer,
        country=body.country,
        market_type=body.market_type,
        notes=body.notes,
        scheduled_at=body.scheduled_at,
    )
    return await ShipmentRepository(session).create(shipment)


@router.get("/{shipment_id}", response_model=ShipmentRead)
async def get_shipment(shipment_id: str, session: AsyncSession = Depends(get_session)):
    shipment = await ShipmentRepository(session).get_by_id(shipment_id)
    if not shipment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipment not found")
    return shipment


@router.patch("/{shipment_id}/status", response_model=ShipmentRead)
async def update_shipment_status(
    shipment_id: str,
    body: ShipmentStatusUpdate,
    session: AsyncSession = Depends(get_session),
):
    repo = ShipmentRepository(session)
    shipment = await repo.get_by_id(shipment_id)
    if not shipment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipment not found")
    try:
        ShipmentStatusService.transition(shipment.status, body.new_status)
    except InvalidShipmentTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return await repo.update_status(shipment_id, body.new_status)


@router.post("/{shipment_id}/labels", response_model=dict)
async def add_labels_to_shipment(
    shipment_id: str,
    body: ShipmentLabelsAdd,
    session: AsyncSession = Depends(get_session),
):
    shipment = await ShipmentRepository(session).get_by_id(shipment_id)
    if not shipment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipment not found")
    load_item_repo = LoadItemRepository(session)
    added = 0
    for progressivo in body.progressivos:
        item = LoadItem(shipment_id=shipment_id, stock_label_id=progressivo)
        await load_item_repo.create(item)
        added += 1
    return {"added": added}


@router.get("/{shipment_id}/labels", response_model=list[LoadItemRead])
async def get_shipment_labels(shipment_id: str, session: AsyncSession = Depends(get_session)):
    shipment = await ShipmentRepository(session).get_by_id(shipment_id)
    if not shipment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipment not found")
    return await LoadItemRepository(session).list_by_shipment(shipment_id)


@router.delete("/{shipment_id}/labels", response_model=dict)
async def remove_labels_from_shipment(shipment_id: str, session: AsyncSession = Depends(get_session)):
    shipment = await ShipmentRepository(session).get_by_id(shipment_id)
    if not shipment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipment not found")
    removed = await LoadItemRepository(session).delete_by_shipment(shipment_id)
    return {"removed": removed}
