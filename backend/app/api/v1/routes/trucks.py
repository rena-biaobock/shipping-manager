from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.truck import Truck
from app.repositories.truck_repository import TruckRepository
from app.schemas.truck import TruckCreate, TruckRead

router = APIRouter(prefix="/trucks", tags=["trucks"])


@router.get("", response_model=list[TruckRead])
async def list_trucks(session: AsyncSession = Depends(get_session)):
    return await TruckRepository(session).list_active()


@router.post("", response_model=TruckRead, status_code=status.HTTP_201_CREATED)
async def create_truck(body: TruckCreate, session: AsyncSession = Depends(get_session)):
    truck = Truck(name=body.name, plate=body.plate, max_weight_tons=body.max_weight_tons)
    return await TruckRepository(session).create(truck)


@router.get("/{truck_id}", response_model=TruckRead)
async def get_truck(truck_id: str, session: AsyncSession = Depends(get_session)):
    truck = await TruckRepository(session).get_by_id(truck_id)
    if not truck:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Truck not found")
    return truck


@router.delete("/{truck_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_truck(truck_id: str, session: AsyncSession = Depends(get_session)):
    if not await TruckRepository(session).deactivate(truck_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Truck not found")
