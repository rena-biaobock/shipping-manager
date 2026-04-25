import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.stock_label import StockLabel
from app.repositories.location_repository import LocationRepository
from app.repositories.stock_label_repository import StockLabelRepository


@pytest.fixture
def repo(session: AsyncSession) -> StockLabelRepository:
    return StockLabelRepository(session)


@pytest.fixture
def location_repo(session: AsyncSession) -> LocationRepository:
    return LocationRepository(session)


def make_label(progressivo: str = "LAB-001", status: str = "available", market_type: str = "ME") -> StockLabel:
    return StockLabel(
        progressivo=progressivo,
        item_code="ITEM-01",
        description="60,30x3,00x6000-NBR5580",
        market_type=market_type,
        volume_tons=0.322,
        piece_count=694,
        status=status,
    )


async def test_create_and_get_label(repo):
    label = await repo.create(make_label("PRG-001"))
    fetched = await repo.get_by_progressivo("PRG-001")
    assert fetched is not None
    assert fetched.progressivo == "PRG-001"
    assert fetched.status == "available"


async def test_get_by_progressivo_unknown_returns_none(repo):
    result = await repo.get_by_progressivo("nonexistent")
    assert result is None


async def test_list_by_status_filters_correctly(repo):
    await repo.create(make_label("A", status="available"))
    await repo.create(make_label("B", status="reserved"))
    await repo.create(make_label("C", status="available"))

    available = await repo.list_by_status("available")
    progressivos = {l.progressivo for l in available}
    assert "A" in progressivos
    assert "C" in progressivos
    assert "B" not in progressivos


async def test_list_by_market_type(repo):
    await repo.create(make_label("ME-1", market_type="ME"))
    await repo.create(make_label("MI-1", market_type="MI"))

    me_labels = await repo.list_by_market_type("ME")
    progressivos = {l.progressivo for l in me_labels}
    assert "ME-1" in progressivos
    assert "MI-1" not in progressivos


async def test_update_status(repo):
    await repo.create(make_label("UPD-01"))
    updated = await repo.update_status("UPD-01", "reserved")
    assert updated is not None
    assert updated.status == "reserved"


async def test_update_status_unknown_returns_none(repo):
    result = await repo.update_status("nonexistent", "reserved")
    assert result is None


async def test_update_location(repo, location_repo):
    await repo.create(make_label("LOC-01"))
    loc = await location_repo.create("Terminal 01 Stock")
    updated = await repo.update_location("LOC-01", loc.id)
    assert updated is not None
    assert updated.location_id == loc.id


async def test_list_by_location(repo, location_repo):
    loc = await location_repo.create("Terminal 02 Stock")
    await repo.create(make_label("T2-A"))
    await repo.create(make_label("T2-B"))
    await repo.update_location("T2-A", loc.id)
    await repo.update_location("T2-B", loc.id)

    labels = await repo.list_by_location(loc.id)
    progressivos = {l.progressivo for l in labels}
    assert progressivos == {"T2-A", "T2-B"}
