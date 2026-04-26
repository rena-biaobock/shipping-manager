from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shipment import Shipment


class ShipmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, shipment: Shipment) -> Shipment:
        self._session.add(shipment)
        await self._session.flush()
        return shipment

    async def get_by_id(self, shipment_id: str) -> Shipment | None:
        return await self._session.get(Shipment, shipment_id)

    async def list_by_status(self, status: str) -> list[Shipment]:
        result = await self._session.execute(
            select(Shipment).where(Shipment.status == status)
        )
        return list(result.scalars().all())

    async def update_status(self, shipment_id: str, new_status: str) -> Shipment | None:
        shipment = await self.get_by_id(shipment_id)
        if shipment:
            shipment.status = new_status
            await self._session.flush()
        return shipment
