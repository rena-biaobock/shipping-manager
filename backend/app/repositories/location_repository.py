from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.location import Location


class LocationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, name: str) -> Location:
        location = Location(name=name)
        self._session.add(location)
        await self._session.flush()
        return location

    async def get_by_id(self, location_id: str) -> Location | None:
        return await self._session.get(Location, location_id)

    async def get_by_name(self, name: str) -> Location | None:
        result = await self._session.execute(select(Location).where(Location.name == name))
        return result.scalar_one_or_none()

    async def list_active(self) -> list[Location]:
        result = await self._session.execute(select(Location).where(Location.active.is_(True)))
        return list(result.scalars().all())

    async def deactivate(self, location_id: str) -> Location | None:
        location = await self.get_by_id(location_id)
        if location:
            location.active = False
            await self._session.flush()
        return location
