from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.truck import Truck


class TruckRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, truck: Truck) -> Truck:
        self._session.add(truck)
        await self._session.flush()
        return truck

    async def get_by_id(self, truck_id: str) -> Truck | None:
        return await self._session.get(Truck, truck_id)

    async def list_active(self) -> list[Truck]:
        result = await self._session.execute(
            select(Truck).where(Truck.active.is_(True))
        )
        return list(result.scalars().all())

    async def deactivate(self, truck_id: str) -> Truck | None:
        truck = await self.get_by_id(truck_id)
        if truck:
            truck.active = False
            await self._session.flush()
        return truck
