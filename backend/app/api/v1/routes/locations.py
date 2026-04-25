from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.repositories.location_repository import LocationRepository
from app.schemas.location import LocationCreate, LocationRead

router = APIRouter(prefix="/locations", tags=["locations"])


@router.get("", response_model=list[LocationRead])
async def list_locations(session: AsyncSession = Depends(get_session)):
    return await LocationRepository(session).list_active()


@router.post("", response_model=LocationRead, status_code=status.HTTP_201_CREATED)
async def create_location(body: LocationCreate, session: AsyncSession = Depends(get_session)):
    repo = LocationRepository(session)
    if await repo.get_by_name(body.name):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Location name already exists")
    return await repo.create(body.name)


@router.get("/{location_id}", response_model=LocationRead)
async def get_location(location_id: str, session: AsyncSession = Depends(get_session)):
    location = await LocationRepository(session).get_by_id(location_id)
    if not location:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")
    return location


@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_location(location_id: str, session: AsyncSession = Depends(get_session)):
    if not await LocationRepository(session).deactivate(location_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")
