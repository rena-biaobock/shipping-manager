import pytest
import httpx


async def test_list_locations_empty(client: httpx.AsyncClient):
    response = await client.get("/api/v1/locations")
    assert response.status_code == 200
    assert response.json() == []


async def test_create_location(client: httpx.AsyncClient):
    response = await client.post("/api/v1/locations", json={"name": "Company Stock"})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Company Stock"
    assert data["active"] is True
    assert "id" in data


async def test_create_location_duplicate_returns_409(client: httpx.AsyncClient):
    await client.post("/api/v1/locations", json={"name": "Terminal 01"})
    response = await client.post("/api/v1/locations", json={"name": "Terminal 01"})
    assert response.status_code == 409


async def test_get_location_by_id(client: httpx.AsyncClient):
    created = (await client.post("/api/v1/locations", json={"name": "Terminal 02"})).json()
    response = await client.get(f"/api/v1/locations/{created['id']}")
    assert response.status_code == 200
    assert response.json()["name"] == "Terminal 02"


async def test_get_location_not_found(client: httpx.AsyncClient):
    response = await client.get("/api/v1/locations/nonexistent-id")
    assert response.status_code == 404


async def test_deactivate_location(client: httpx.AsyncClient):
    created = (await client.post("/api/v1/locations", json={"name": "To Remove"})).json()
    response = await client.delete(f"/api/v1/locations/{created['id']}")
    assert response.status_code == 204


async def test_deactivated_location_excluded_from_list(client: httpx.AsyncClient):
    created = (await client.post("/api/v1/locations", json={"name": "Will Be Inactive"})).json()
    await client.delete(f"/api/v1/locations/{created['id']}")
    response = await client.get("/api/v1/locations")
    names = [loc["name"] for loc in response.json()]
    assert "Will Be Inactive" not in names


async def test_deactivate_location_not_found(client: httpx.AsyncClient):
    response = await client.delete("/api/v1/locations/nonexistent-id")
    assert response.status_code == 404
