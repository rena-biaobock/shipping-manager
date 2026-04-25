import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order
from app.repositories.order_repository import OrderRepository


@pytest.fixture
def repo(session: AsyncSession) -> OrderRepository:
    return OrderRepository(session)


def make_order(order_number: str = "PED-001", market_type: str = "ME", country: str = "Paraguay") -> Order:
    return Order(order_number=order_number, market_type=market_type, country=country, condition="pedido_ate_hoje")


async def test_create_and_get_order(repo):
    order = await repo.create(make_order("PED-100"))
    fetched = await repo.get_by_id(order.id)
    assert fetched is not None
    assert fetched.order_number == "PED-100"


async def test_get_by_id_unknown_returns_none(repo):
    assert await repo.get_by_id("nonexistent") is None


async def test_get_by_order_number(repo):
    await repo.create(make_order("PED-200"))
    fetched = await repo.get_by_order_number("PED-200")
    assert fetched is not None
    assert fetched.order_number == "PED-200"


async def test_get_by_order_number_unknown_returns_none(repo):
    assert await repo.get_by_order_number("PED-XXXX") is None


async def test_list_by_market_type(repo):
    await repo.create(make_order("PED-ME", market_type="ME"))
    await repo.create(make_order("PED-MI", market_type="MI"))
    me_orders = await repo.list_by_market_type("ME")
    numbers = {o.order_number for o in me_orders}
    assert "PED-ME" in numbers
    assert "PED-MI" not in numbers


async def test_list_by_country(repo):
    await repo.create(make_order("PED-PY", country="Paraguay"))
    await repo.create(make_order("PED-BR", country="Brasil"))
    py_orders = await repo.list_by_country("Paraguay")
    numbers = {o.order_number for o in py_orders}
    assert "PED-PY" in numbers
    assert "PED-BR" not in numbers
