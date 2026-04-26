from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.load_item import LoadItem


class LoadItemRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, load_item: LoadItem) -> LoadItem:
        self._session.add(load_item)
        await self._session.flush()
        return load_item

    async def list_by_shipment(self, shipment_id: str) -> list[LoadItem]:
        result = await self._session.execute(
            select(LoadItem).where(LoadItem.shipment_id == shipment_id)
        )
        return list(result.scalars().all())

    async def delete_by_shipment(self, shipment_id: str) -> int:
        items = await self.list_by_shipment(shipment_id)
        for item in items:
            await self._session.delete(item)
        await self._session.flush()
        return len(items)
