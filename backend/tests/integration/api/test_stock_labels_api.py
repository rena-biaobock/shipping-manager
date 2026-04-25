"""
Integration tests for the Stock Labels API.

Endpoints:
  GET    /api/v1/stock-labels                         list with optional filters
  GET    /api/v1/stock-labels/{progressivo}           get single label
  PATCH  /api/v1/stock-labels/{progressivo}/status    status transition
  PATCH  /api/v1/stock-labels/{progressivo}/location  move to a location (records history)
"""

import pytest
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.stock_label import StockLabel
from app.repositories.label_location_history_repository import LabelLocationHistoryRepository
from app.repositories.location_repository import LocationRepository
from app.repositories.stock_label_repository import StockLabelRepository


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def seed_label(session: AsyncSession, progressivo: str, status: str = "available", market_type: str = "ME") -> StockLabel:
    repo = StockLabelRepository(session)
    return await repo.create(StockLabel(
        progressivo=progressivo,
        item_code="ITEM-01",
        description="60,30x3,00x6000",
        market_type=market_type,
        volume_tons=0.322,
        piece_count=10,
        status=status,
    ))


async def seed_location(session: AsyncSession, name: str) -> str:
    loc = await LocationRepository(session).create(name)
    return loc.id


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------

async def test_list_stock_labels_empty(client: httpx.AsyncClient):
    response = await client.get("/api/v1/stock-labels")
    assert response.status_code == 200
    assert response.json() == []


async def test_list_stock_labels_returns_all(client: httpx.AsyncClient, session: AsyncSession):
    await seed_label(session, "PRG-L01")
    await seed_label(session, "PRG-L02")
    response = await client.get("/api/v1/stock-labels")
    progressivos = {l["progressivo"] for l in response.json()}
    assert {"PRG-L01", "PRG-L02"}.issubset(progressivos)


async def test_list_stock_labels_filter_by_status(client: httpx.AsyncClient, session: AsyncSession):
    await seed_label(session, "PRG-AV1", status="available")
    await seed_label(session, "PRG-RS1", status="reserved")
    response = await client.get("/api/v1/stock-labels?status=available")
    statuses = {l["status"] for l in response.json()}
    assert statuses == {"available"}


async def test_list_stock_labels_filter_by_market_type(client: httpx.AsyncClient, session: AsyncSession):
    await seed_label(session, "PRG-ME1", market_type="ME")
    await seed_label(session, "PRG-MI1", market_type="MI")
    response = await client.get("/api/v1/stock-labels?market_type=ME")
    market_types = {l["market_type"] for l in response.json()}
    assert market_types == {"ME"}


# ---------------------------------------------------------------------------
# Get single
# ---------------------------------------------------------------------------

async def test_get_stock_label(client: httpx.AsyncClient, session: AsyncSession):
    await seed_label(session, "PRG-GET1")
    response = await client.get("/api/v1/stock-labels/PRG-GET1")
    assert response.status_code == 200
    assert response.json()["progressivo"] == "PRG-GET1"


async def test_get_stock_label_not_found(client: httpx.AsyncClient):
    response = await client.get("/api/v1/stock-labels/NONEXISTENT")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Status update
# ---------------------------------------------------------------------------

async def test_update_status_valid_transition(client: httpx.AsyncClient, session: AsyncSession):
    await seed_label(session, "PRG-ST1", status="available")
    response = await client.patch("/api/v1/stock-labels/PRG-ST1/status", json={"new_status": "reserved"})
    assert response.status_code == 200
    assert response.json()["status"] == "reserved"


async def test_update_status_invalid_transition_returns_422(client: httpx.AsyncClient, session: AsyncSession):
    await seed_label(session, "PRG-ST2", status="available")
    response = await client.patch("/api/v1/stock-labels/PRG-ST2/status", json={"new_status": "delivered"})
    assert response.status_code == 422


async def test_update_status_label_not_found(client: httpx.AsyncClient):
    response = await client.patch("/api/v1/stock-labels/NONEXISTENT/status", json={"new_status": "reserved"})
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Location update
# ---------------------------------------------------------------------------

async def test_update_location_sets_location_id(client: httpx.AsyncClient, session: AsyncSession):
    await seed_label(session, "PRG-LOC1")
    loc_id = await seed_location(session, "Terminal 01 API")
    response = await client.patch("/api/v1/stock-labels/PRG-LOC1/location", json={"location_id": loc_id})
    assert response.status_code == 200
    assert response.json()["location_id"] == loc_id


async def test_update_location_records_history(client: httpx.AsyncClient, session: AsyncSession):
    await seed_label(session, "PRG-LOC2")
    loc_id = await seed_location(session, "Terminal 02 API")
    await client.patch("/api/v1/stock-labels/PRG-LOC2/location", json={"location_id": loc_id})
    history = await LabelLocationHistoryRepository(session).get_history("PRG-LOC2")
    assert len(history) == 1
    assert history[0].to_location_id == loc_id


async def test_update_location_label_not_found(client: httpx.AsyncClient, session: AsyncSession):
    loc_id = await seed_location(session, "Terminal 03 API")
    response = await client.patch("/api/v1/stock-labels/NONEXISTENT/location", json={"location_id": loc_id})
    assert response.status_code == 404
