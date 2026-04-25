from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.label_location_history import LabelLocationHistory


class LabelLocationHistoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record(
        self,
        progressivo: str,
        to_location_id: str,
        from_location_id: str | None = None,
    ) -> LabelLocationHistory:
        entry = LabelLocationHistory(
            progressivo=progressivo,
            from_location_id=from_location_id,
            to_location_id=to_location_id,
        )
        self._session.add(entry)
        await self._session.flush()
        return entry

    async def get_history(self, progressivo: str) -> list[LabelLocationHistory]:
        result = await self._session.execute(
            select(LabelLocationHistory)
            .where(LabelLocationHistory.progressivo == progressivo)
            .order_by(LabelLocationHistory.moved_at)
        )
        return list(result.scalars().all())
