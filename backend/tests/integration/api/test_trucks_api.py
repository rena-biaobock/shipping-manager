import pytest
import httpx


async def test_list_trucks_empty(client: httpx.AsyncClient):
    response = await client.get("/api/v1/trucks")
    assert response.status_code == 200
    assert response.json() == []


async def test_create_truck(client: httpx.AsyncClient):
    response = await client.post("/api/v1/trucks", json={"name": "Truck 01", "max_weight_tons": "28.5"})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Truck 01"
    assert float(data["max_weight_tons"]) == 28.5
    assert data["active"] is True
    assert "id" in data


async def test_create_truck_with_plate(client: httpx.AsyncClient):
    response = await client.post("/api/v1/trucks", json={"name": "Truck 02", "plate": "ABC-1234", "max_weight_tons": "30.0"})
    assert response.status_code == 201
    assert response.json()["plate"] == "ABC-1234"


async def test_get_truck_by_id(client: httpx.AsyncClient):
    created = (await client.post("/api/v1/trucks", json={"name": "Truck 03", "max_weight_tons": "25.0"})).json()
    response = await client.get(f"/api/v1/trucks/{created['id']}")
    assert response.status_code == 200
    assert response.json()["name"] == "Truck 03"


async def test_get_truck_not_found(client: httpx.AsyncClient):
    response = await client.get("/api/v1/trucks/nonexistent-id")
    assert response.status_code == 404


async def test_deactivate_truck(client: httpx.AsyncClient):
    created = (await client.post("/api/v1/trucks", json={"name": "Truck To Remove", "max_weight_tons": "20.0"})).json()
    response = await client.delete(f"/api/v1/trucks/{created['id']}")
    assert response.status_code == 204


async def test_deactivated_truck_excluded_from_list(client: httpx.AsyncClient):
    created = (await client.post("/api/v1/trucks", json={"name": "Will Be Inactive", "max_weight_tons": "15.0"})).json()
    await client.delete(f"/api/v1/trucks/{created['id']}")
    response = await client.get("/api/v1/trucks")
    names = [t["name"] for t in response.json()]
    assert "Will Be Inactive" not in names


async def test_deactivate_truck_not_found(client: httpx.AsyncClient):
    response = await client.delete("/api/v1/trucks/nonexistent-id")
    assert response.status_code == 404
