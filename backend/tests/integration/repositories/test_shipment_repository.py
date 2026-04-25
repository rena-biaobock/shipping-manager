import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shipment import Shipment
from app.models.truck import Truck
from app.repositories.shipment_repository import ShipmentRepository
from app.repositories.truck_repository import TruckRepository


@pytest.fixture
def repo(session: AsyncSession) -> ShipmentRepository:
    return ShipmentRepository(session)


@pytest.fixture
def truck_repo(session: AsyncSession) -> TruckRepository:
    return TruckRepository(session)


async def test_create_and_get_shipment(repo):
    shipment = await repo.create(Shipment(destination="Terminal 01", market_type="ME"))
    fetched = await repo.get_by_id(shipment.id)
    assert fetched is not None
    assert fetched.status == "draft"
    assert fetched.destination == "Terminal 01"


async def test_get_by_id_unknown_returns_none(repo):
    assert await repo.get_by_id("nonexistent") is None


async def test_list_by_status(repo):
    await repo.create(Shipment(status="draft"))
    await repo.create(Shipment(status="confirmed"))
    await repo.create(Shipment(status="draft"))

    drafts = await repo.list_by_status("draft")
    assert len(drafts) >= 2
    assert all(s.status == "draft" for s in drafts)


async def test_update_status(repo):
    shipment = await repo.create(Shipment(status="draft"))
    updated = await repo.update_status(shipment.id, "confirmed")
    assert updated is not None
    assert updated.status == "confirmed"


async def test_update_status_unknown_returns_none(repo):
    assert await repo.update_status("nonexistent", "confirmed") is None


async def test_shipment_linked_to_truck(repo, truck_repo):
    truck = await truck_repo.create(Truck(name="Truck B", max_weight_tons=25.0))
    shipment = await repo.create(Shipment(truck_id=truck.id, status="draft"))
    fetched = await repo.get_by_id(shipment.id)
    assert fetched.truck_id == truck.id
