from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.stock_label import StockLabel


class StockLabelRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, label: StockLabel) -> StockLabel:
        self._session.add(label)
        await self._session.flush()
        return label

    async def get_by_progressivo(self, progressivo: str) -> StockLabel | None:
        return await self._session.get(StockLabel, progressivo)

    async def list_by_status(self, status: str) -> list[StockLabel]:
        result = await self._session.execute(
            select(StockLabel).where(StockLabel.status == status)
        )
        return list(result.scalars().all())

    async def list_by_location(self, location_id: str) -> list[StockLabel]:
        result = await self._session.execute(
            select(StockLabel).where(StockLabel.location_id == location_id)
        )
        return list(result.scalars().all())

    async def list_by_market_type(self, market_type: str) -> list[StockLabel]:
        result = await self._session.execute(
            select(StockLabel).where(StockLabel.market_type == market_type)
        )
        return list(result.scalars().all())

    async def update_status(self, progressivo: str, new_status: str) -> StockLabel | None:
        label = await self.get_by_progressivo(progressivo)
        if label:
            label.status = new_status
            await self._session.flush()
        return label

    async def update_location(self, progressivo: str, location_id: str | None) -> StockLabel | None:
        label = await self.get_by_progressivo(progressivo)
        if label:
            label.location_id = location_id
            await self._session.flush()
        return label
