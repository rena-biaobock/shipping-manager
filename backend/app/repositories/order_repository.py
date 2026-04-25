from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order


class OrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, order: Order) -> Order:
        self._session.add(order)
        await self._session.flush()
        return order

    async def get_by_id(self, order_id: str) -> Order | None:
        return await self._session.get(Order, order_id)

    async def get_by_order_number(self, order_number: str) -> Order | None:
        result = await self._session.execute(
            select(Order).where(Order.order_number == order_number)
        )
        return result.scalar_one_or_none()

    async def list_by_market_type(self, market_type: str) -> list[Order]:
        result = await self._session.execute(
            select(Order).where(Order.market_type == market_type)
        )
        return list(result.scalars().all())

    async def list_by_country(self, country: str) -> list[Order]:
        result = await self._session.execute(
            select(Order).where(Order.country == country)
        )
        return list(result.scalars().all())
