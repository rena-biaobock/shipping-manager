"""
Integration tests for the Shipments API.

Endpoints:
  GET    /api/v1/shipments                      list with optional status filter
  POST   /api/v1/shipments                      create a new draft shipment
  GET    /api/v1/shipments/{shipment_id}         get single shipment
  PATCH  /api/v1/shipments/{shipment_id}/status  status transition
  POST   /api/v1/shipments/{shipment_id}/labels  add labels to a shipment
  DELETE /api/v1/shipments/{shipment_id}/labels  remove all labels from a shipment
  GET    /api/v1/shipments/{shipment_id}/labels  list labels assigned to a shipment
"""

import pytest
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shipment import Shipment
from app.models.stock_label import StockLabel
from app.models.truck import Truck
from app.repositories.load_item_repository import LoadItemRepository
from app.repositories.shipment_repository import ShipmentRepository
from app.repositories.stock_label_repository import StockLabelRepository
from app.repositories.truck_repository import TruckRepository


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def seed_truck(session: AsyncSession, name: str = "Truck A", max_weight_tons: float = 30.0) -> Truck:
    truck = Truck(name=name, plate=None, max_weight_tons=max_weight_tons)
    return await TruckRepository(session).create(truck)


async def seed_shipment(session: AsyncSession, truck_id: str, status: str = "draft") -> Shipment:
    shipment = Shipment(truck_id=truck_id, status=status, destination="Porto Alegre", customer="Acme")
    return await ShipmentRepository(session).create(shipment)


async def seed_label(session: AsyncSession, progressivo: str, status: str = "available") -> StockLabel:
    label = StockLabel(
        progressivo=progressivo,
        item_code="ITEM-01",
        description="60,30x3,00x6000",
        market_type="ME",
        volume_tons=1.5,
        piece_count=5,
        status=status,
    )
    return await StockLabelRepository(session).create(label)


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------

async def test_list_shipments_empty(client: httpx.AsyncClient):
    response = await client.get("/api/v1/shipments")
    assert response.status_code == 200
    assert response.json() == []


async def test_list_shipments_returns_all(client: httpx.AsyncClient, session: AsyncSession):
    truck = await seed_truck(session)
    await seed_shipment(session, truck.id, status="draft")
    await seed_shipment(session, truck.id, status="confirmed")
    response = await client.get("/api/v1/shipments")
    assert len(response.json()) >= 2


async def test_list_shipments_filter_by_status(client: httpx.AsyncClient, session: AsyncSession):
    truck = await seed_truck(session, name="Truck Filter")
    await seed_shipment(session, truck.id, status="draft")
    await seed_shipment(session, truck.id, status="dispatched")
    response = await client.get("/api/v1/shipments?status=draft")
    statuses = {s["status"] for s in response.json()}
    assert statuses == {"draft"}


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

async def test_create_shipment_returns_201(client: httpx.AsyncClient, session: AsyncSession):
    truck = await seed_truck(session, name="Truck Create")
    response = await client.post("/api/v1/shipments", json={
        "truck_id": truck.id,
        "destination": "Montevideo",
        "customer": "Cliente X",
    })
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "draft"
    assert body["truck_id"] == truck.id


async def test_create_shipment_with_unknown_truck_returns_404(client: httpx.AsyncClient):
    response = await client.post("/api/v1/shipments", json={
        "truck_id": "00000000-0000-0000-0000-000000000000",
        "destination": "Somewhere",
    })
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Get single
# ---------------------------------------------------------------------------

async def test_get_shipment(client: httpx.AsyncClient, session: AsyncSession):
    truck = await seed_truck(session, name="Truck Get")
    shipment = await seed_shipment(session, truck.id)
    response = await client.get(f"/api/v1/shipments/{shipment.id}")
    assert response.status_code == 200
    assert response.json()["id"] == shipment.id


async def test_get_shipment_not_found(client: httpx.AsyncClient):
    response = await client.get("/api/v1/shipments/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Status update
# ---------------------------------------------------------------------------

async def test_update_shipment_status_valid_transition(client: httpx.AsyncClient, session: AsyncSession):
    truck = await seed_truck(session, name="Truck Status")
    shipment = await seed_shipment(session, truck.id, status="draft")
    response = await client.patch(f"/api/v1/shipments/{shipment.id}/status", json={"new_status": "confirmed"})
    assert response.status_code == 200
    assert response.json()["status"] == "confirmed"


async def test_update_shipment_status_invalid_transition_returns_422(client: httpx.AsyncClient, session: AsyncSession):
    truck = await seed_truck(session, name="Truck Bad Transition")
    shipment = await seed_shipment(session, truck.id, status="draft")
    response = await client.patch(f"/api/v1/shipments/{shipment.id}/status", json={"new_status": "delivered"})
    assert response.status_code == 422


async def test_update_shipment_status_not_found(client: httpx.AsyncClient):
    response = await client.patch(
        "/api/v1/shipments/00000000-0000-0000-0000-000000000000/status",
        json={"new_status": "confirmed"},
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Labels in shipment
# ---------------------------------------------------------------------------

async def test_add_labels_to_shipment(client: httpx.AsyncClient, session: AsyncSession):
    truck = await seed_truck(session, name="Truck Labels Add")
    shipment = await seed_shipment(session, truck.id)
    await seed_label(session, "PRG-SH1")
    await seed_label(session, "PRG-SH2")
    response = await client.post(
        f"/api/v1/shipments/{shipment.id}/labels",
        json={"progressivos": ["PRG-SH1", "PRG-SH2"]},
    )
    assert response.status_code == 200
    assert response.json()["added"] == 2


async def test_add_labels_to_shipment_not_found(client: httpx.AsyncClient):
    response = await client.post(
        "/api/v1/shipments/00000000-0000-0000-0000-000000000000/labels",
        json={"progressivos": ["PRG-X"]},
    )
    assert response.status_code == 404


async def test_get_shipment_labels(client: httpx.AsyncClient, session: AsyncSession):
    truck = await seed_truck(session, name="Truck Labels List")
    shipment = await seed_shipment(session, truck.id)
    await seed_label(session, "PRG-SH3")
    await client.post(
        f"/api/v1/shipments/{shipment.id}/labels",
        json={"progressivos": ["PRG-SH3"]},
    )
    response = await client.get(f"/api/v1/shipments/{shipment.id}/labels")
    assert response.status_code == 200
    progressivos = [item["stock_label_id"] for item in response.json()]
    assert "PRG-SH3" in progressivos


async def test_remove_labels_from_shipment(client: httpx.AsyncClient, session: AsyncSession):
    truck = await seed_truck(session, name="Truck Labels Del")
    shipment = await seed_shipment(session, truck.id)
    await seed_label(session, "PRG-SH4")
    await client.post(
        f"/api/v1/shipments/{shipment.id}/labels",
        json={"progressivos": ["PRG-SH4"]},
    )
    response = await client.delete(f"/api/v1/shipments/{shipment.id}/labels")
    assert response.status_code == 200
    assert response.json()["removed"] >= 1
    items = await LoadItemRepository(session).list_by_shipment(shipment.id)
    assert items == []
