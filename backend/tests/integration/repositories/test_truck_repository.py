import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.truck import Truck
from app.repositories.truck_repository import TruckRepository


@pytest.fixture
def repo(session: AsyncSession) -> TruckRepository:
    return TruckRepository(session)


def make_truck(name: str = "Truck 01", plate: str | None = None) -> Truck:
    return Truck(name=name, plate=plate, max_weight_tons=30.0)


async def test_create_and_get_truck(repo):
    truck = await repo.create(make_truck("Truck A"))
    fetched = await repo.get_by_id(truck.id)
    assert fetched is not None
    assert fetched.name == "Truck A"
    assert fetched.active is True


async def test_get_by_id_unknown_returns_none(repo):
    assert await repo.get_by_id("nonexistent") is None


async def test_list_active_excludes_inactive(repo):
    active = await repo.create(make_truck("Active Truck"))
    inactive = await repo.create(make_truck("Inactive Truck"))
    await repo.deactivate(inactive.id)

    trucks = await repo.list_active()
    names = [t.name for t in trucks]
    assert "Active Truck" in names
    assert "Inactive Truck" not in names


async def test_deactivate_sets_active_false(repo):
    truck = await repo.create(make_truck("To Deactivate"))
    result = await repo.deactivate(truck.id)
    assert result is not None
    assert result.active is False


async def test_deactivate_unknown_returns_none(repo):
    assert await repo.deactivate("nonexistent") is None
