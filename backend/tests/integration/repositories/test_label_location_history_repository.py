import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.stock_label import StockLabel
from app.repositories.label_location_history_repository import LabelLocationHistoryRepository
from app.repositories.location_repository import LocationRepository
from app.repositories.stock_label_repository import StockLabelRepository


@pytest.fixture
def history_repo(session: AsyncSession) -> LabelLocationHistoryRepository:
    return LabelLocationHistoryRepository(session)


@pytest.fixture
def location_repo(session: AsyncSession) -> LocationRepository:
    return LocationRepository(session)


@pytest.fixture
def label_repo(session: AsyncSession) -> StockLabelRepository:
    return StockLabelRepository(session)


async def test_record_creates_history_entry(history_repo, location_repo, label_repo):
    label = StockLabel(progressivo="H-001", item_code="I", description="D", market_type="ME", volume_tons=1.0, piece_count=1, status="available")
    await label_repo.create(label)
    loc = await location_repo.create("Company Stock")

    entry = await history_repo.record("H-001", to_location_id=loc.id)
    assert entry.id is not None
    assert entry.progressivo == "H-001"
    assert entry.to_location_id == loc.id
    assert entry.from_location_id is None


async def test_record_with_from_location(history_repo, location_repo, label_repo):
    label = StockLabel(progressivo="H-002", item_code="I", description="D", market_type="ME", volume_tons=1.0, piece_count=1, status="available")
    await label_repo.create(label)
    loc_a = await location_repo.create("Company Stock A")
    loc_b = await location_repo.create("Terminal 01 A")

    entry = await history_repo.record("H-002", to_location_id=loc_b.id, from_location_id=loc_a.id)
    assert entry.from_location_id == loc_a.id
    assert entry.to_location_id == loc_b.id


async def test_get_history_returns_entries_in_order(history_repo, location_repo, label_repo):
    label = StockLabel(progressivo="H-003", item_code="I", description="D", market_type="ME", volume_tons=1.0, piece_count=1, status="available")
    await label_repo.create(label)
    loc_a = await location_repo.create("Company Stock B")
    loc_b = await location_repo.create("Terminal 03")

    await history_repo.record("H-003", to_location_id=loc_a.id)
    await history_repo.record("H-003", to_location_id=loc_b.id, from_location_id=loc_a.id)

    history = await history_repo.get_history("H-003")
    assert len(history) == 2
    assert history[0].to_location_id == loc_a.id
    assert history[1].to_location_id == loc_b.id


async def test_get_history_unknown_label_returns_empty(history_repo):
    history = await history_repo.get_history("nonexistent")
    assert history == []
