import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.location_repository import LocationRepository


@pytest.fixture
def repo(session: AsyncSession) -> LocationRepository:
    return LocationRepository(session)


async def test_create_location(repo):
    loc = await repo.create("Company Stock")
    assert loc.id is not None
    assert loc.name == "Company Stock"
    assert loc.active is True


async def test_get_by_id_returns_location(repo):
    loc = await repo.create("Terminal 01")
    fetched = await repo.get_by_id(loc.id)
    assert fetched is not None
    assert fetched.name == "Terminal 01"


async def test_get_by_id_unknown_returns_none(repo):
    result = await repo.get_by_id("nonexistent-id")
    assert result is None


async def test_get_by_name_returns_location(repo):
    await repo.create("Terminal 02")
    fetched = await repo.get_by_name("Terminal 02")
    assert fetched is not None
    assert fetched.name == "Terminal 02"


async def test_get_by_name_unknown_returns_none(repo):
    result = await repo.get_by_name("Does Not Exist")
    assert result is None


async def test_list_active_excludes_inactive(repo):
    active = await repo.create("Active Location")
    inactive = await repo.create("Inactive Location")
    await repo.deactivate(inactive.id)

    active_locations = await repo.list_active()
    names = [l.name for l in active_locations]
    assert "Active Location" in names
    assert "Inactive Location" not in names


async def test_deactivate_sets_active_false(repo):
    loc = await repo.create("To Deactivate")
    result = await repo.deactivate(loc.id)
    assert result is not None
    assert result.active is False


async def test_deactivate_unknown_returns_none(repo):
    result = await repo.deactivate("nonexistent-id")
    assert result is None
