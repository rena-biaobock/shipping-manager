import pytest
import httpx
from httpx import ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.base import Base
from app.models.label_location_history import LabelLocationHistory  # noqa: F401
from app.models.load_item import LoadItem  # noqa: F401
from app.models.location import Location  # noqa: F401
from app.models.order import Order  # noqa: F401
from app.models.shipment import Shipment  # noqa: F401
from app.models.stock_label import StockLabel  # noqa: F401
from app.models.truck import Truck  # noqa: F401

DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def engine():
    return create_async_engine(DATABASE_URL, echo=False)


@pytest.fixture(scope="session")
async def create_tables(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def session(engine, create_tables) -> AsyncSession:
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as s:
        async with s.begin():
            yield s
            await s.rollback()


@pytest.fixture
async def client(session: AsyncSession) -> httpx.AsyncClient:
    from app.main import app
    from app.core.database import get_session

    async def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
