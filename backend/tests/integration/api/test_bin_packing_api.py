"""
Integration tests for the Bin-Packing API.

Endpoint:
  POST /api/v1/bin-packing/pack

Request body:
  truck_id       str
  filters        { country?, order_condition?, exit_date_from?, exit_date_to? }
  max_iterations int | null

Response:
  items            list[{ progressivo, volume_tons }]
  total_weight_tons float
  partial          bool
"""

import pytest
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.stock_label import StockLabel
from app.models.truck import Truck
from app.repositories.stock_label_repository import StockLabelRepository
from app.repositories.truck_repository import TruckRepository


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def seed_truck(session: AsyncSession, name: str = "Truck BP", max_weight_tons: float = 30.0) -> Truck:
    truck = Truck(name=name, plate=None, max_weight_tons=max_weight_tons)
    return await TruckRepository(session).create(truck)


async def seed_label(
    session: AsyncSession,
    progressivo: str,
    volume_tons: float = 1.0,
    market_type: str = "ME",
    country: str = "Paraguay",
    order_condition: str = "pedido_ate_hoje",
    exit_date: str | None = None,
    status: str = "available",
) -> StockLabel:
    label = StockLabel(
        progressivo=progressivo,
        item_code="ITEM-01",
        description="60,30x3,00x6000",
        market_type=market_type,
        volume_tons=volume_tons,
        piece_count=5,
        status=status,
        country=country,
        order_condition=order_condition,
        exit_date=exit_date,
    )
    return await StockLabelRepository(session).create(label)


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

async def test_pack_returns_load_plan(client: httpx.AsyncClient, session: AsyncSession):
    truck = await seed_truck(session, "Truck Pack 1", max_weight_tons=10.0)
    await seed_label(session, "BP-01", volume_tons=3.0)
    await seed_label(session, "BP-02", volume_tons=4.0)
    response = await client.post("/api/v1/bin-packing/pack", json={
        "truck_id": truck.id,
        "filters": {},
    })
    assert response.status_code == 200
    body = response.json()
    assert "items" in body
    assert "total_weight_tons" in body
    assert "partial" in body
    assert body["total_weight_tons"] <= 10.0


async def test_pack_respects_truck_capacity(client: httpx.AsyncClient, session: AsyncSession):
    truck = await seed_truck(session, "Truck Cap", max_weight_tons=5.0)
    await seed_label(session, "BP-CAP1", volume_tons=3.0)
    await seed_label(session, "BP-CAP2", volume_tons=3.0)
    response = await client.post("/api/v1/bin-packing/pack", json={
        "truck_id": truck.id,
        "filters": {},
    })
    assert response.status_code == 200
    body = response.json()
    assert body["total_weight_tons"] <= 5.0
    assert len(body["items"]) == 1


async def test_pack_excludes_mi_labels(client: httpx.AsyncClient, session: AsyncSession):
    truck = await seed_truck(session, "Truck MI", max_weight_tons=20.0)
    await seed_label(session, "BP-ME1", volume_tons=2.0, market_type="ME")
    await seed_label(session, "BP-MI1", volume_tons=2.0, market_type="MI")
    response = await client.post("/api/v1/bin-packing/pack", json={
        "truck_id": truck.id,
        "filters": {},
    })
    assert response.status_code == 200
    packed_progressivos = {item["progressivo"] for item in response.json()["items"]}
    assert "BP-ME1" in packed_progressivos
    assert "BP-MI1" not in packed_progressivos


async def test_pack_filter_by_country(client: httpx.AsyncClient, session: AsyncSession):
    truck = await seed_truck(session, "Truck Country", max_weight_tons=20.0)
    await seed_label(session, "BP-PY1", volume_tons=2.0, country="Paraguay")
    await seed_label(session, "BP-AR1", volume_tons=2.0, country="Argentina")
    response = await client.post("/api/v1/bin-packing/pack", json={
        "truck_id": truck.id,
        "filters": {"country": "Paraguay"},
    })
    assert response.status_code == 200
    packed_progressivos = {item["progressivo"] for item in response.json()["items"]}
    assert "BP-PY1" in packed_progressivos
    assert "BP-AR1" not in packed_progressivos


async def test_pack_filter_by_order_condition(client: httpx.AsyncClient, session: AsyncSession):
    truck = await seed_truck(session, "Truck OC", max_weight_tons=20.0)
    await seed_label(session, "BP-OC1", volume_tons=2.0, order_condition="pedido_ate_hoje")
    await seed_label(session, "BP-OC2", volume_tons=2.0, order_condition="fixo_futuro")
    response = await client.post("/api/v1/bin-packing/pack", json={
        "truck_id": truck.id,
        "filters": {"order_condition": "pedido_ate_hoje"},
    })
    assert response.status_code == 200
    packed_progressivos = {item["progressivo"] for item in response.json()["items"]}
    assert "BP-OC1" in packed_progressivos
    assert "BP-OC2" not in packed_progressivos


async def test_pack_filter_by_exit_date_range(client: httpx.AsyncClient, session: AsyncSession):
    truck = await seed_truck(session, "Truck Date", max_weight_tons=20.0)
    await seed_label(session, "BP-D1", volume_tons=2.0, exit_date="2026-03-01")
    await seed_label(session, "BP-D2", volume_tons=2.0, exit_date="2026-06-01")
    response = await client.post("/api/v1/bin-packing/pack", json={
        "truck_id": truck.id,
        "filters": {"exit_date_from": "2026-01-01", "exit_date_to": "2026-04-30"},
    })
    assert response.status_code == 200
    packed_progressivos = {item["progressivo"] for item in response.json()["items"]}
    assert "BP-D1" in packed_progressivos
    assert "BP-D2" not in packed_progressivos


async def test_pack_max_iterations_flags_partial(client: httpx.AsyncClient, session: AsyncSession):
    truck = await seed_truck(session, "Truck Iter", max_weight_tons=100.0)
    for i in range(5):
        await seed_label(session, f"BP-IT{i}", volume_tons=1.0)
    response = await client.post("/api/v1/bin-packing/pack", json={
        "truck_id": truck.id,
        "filters": {},
        "max_iterations": 2,
    })
    assert response.status_code == 200
    body = response.json()
    assert body["partial"] is True


async def test_pack_empty_stock_returns_empty_plan(client: httpx.AsyncClient, session: AsyncSession):
    truck = await seed_truck(session, "Truck Empty")
    response = await client.post("/api/v1/bin-packing/pack", json={
        "truck_id": truck.id,
        "filters": {},
    })
    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert body["total_weight_tons"] == 0.0
    assert body["partial"] is False


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------

async def test_pack_unknown_truck_returns_404(client: httpx.AsyncClient):
    response = await client.post("/api/v1/bin-packing/pack", json={
        "truck_id": "00000000-0000-0000-0000-000000000000",
        "filters": {},
    })
    assert response.status_code == 404
