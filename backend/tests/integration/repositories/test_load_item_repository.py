import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.load_item import LoadItem
from app.models.shipment import Shipment
from app.models.stock_label import StockLabel
from app.repositories.load_item_repository import LoadItemRepository
from app.repositories.shipment_repository import ShipmentRepository
from app.repositories.stock_label_repository import StockLabelRepository


@pytest.fixture
def repo(session: AsyncSession) -> LoadItemRepository:
    return LoadItemRepository(session)


@pytest.fixture
def shipment_repo(session: AsyncSession) -> ShipmentRepository:
    return ShipmentRepository(session)


@pytest.fixture
def label_repo(session: AsyncSession) -> StockLabelRepository:
    return StockLabelRepository(session)


def make_label(progressivo: str) -> StockLabel:
    return StockLabel(progressivo=progressivo, item_code="I", description="D", market_type="ME", volume_tons=1.0, piece_count=1, status="reserved")


async def test_create_load_item(repo, shipment_repo, label_repo):
    shipment = await shipment_repo.create(Shipment(status="confirmed"))
    await label_repo.create(make_label("LI-001"))
    item = await repo.create(LoadItem(shipment_id=shipment.id, stock_label_id="LI-001"))
    assert item.id is not None
    assert item.shipment_id == shipment.id
    assert item.stock_label_id == "LI-001"


async def test_list_by_shipment(repo, shipment_repo, label_repo):
    shipment = await shipment_repo.create(Shipment(status="confirmed"))
    await label_repo.create(make_label("LI-A"))
    await label_repo.create(make_label("LI-B"))
    await repo.create(LoadItem(shipment_id=shipment.id, stock_label_id="LI-A"))
    await repo.create(LoadItem(shipment_id=shipment.id, stock_label_id="LI-B"))

    items = await repo.list_by_shipment(shipment.id)
    assert {i.stock_label_id for i in items} == {"LI-A", "LI-B"}


async def test_list_by_shipment_empty(repo, shipment_repo):
    shipment = await shipment_repo.create(Shipment(status="draft"))
    items = await repo.list_by_shipment(shipment.id)
    assert items == []


async def test_delete_by_shipment_removes_all_items(repo, shipment_repo, label_repo):
    shipment = await shipment_repo.create(Shipment(status="confirmed"))
    await label_repo.create(make_label("LI-DEL-A"))
    await label_repo.create(make_label("LI-DEL-B"))
    await repo.create(LoadItem(shipment_id=shipment.id, stock_label_id="LI-DEL-A"))
    await repo.create(LoadItem(shipment_id=shipment.id, stock_label_id="LI-DEL-B"))

    deleted = await repo.delete_by_shipment(shipment.id)
    assert deleted == 2
    assert await repo.list_by_shipment(shipment.id) == []
