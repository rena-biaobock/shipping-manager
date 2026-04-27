import os
import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("XLSX_PATH", os.path.join(os.path.dirname(__file__), "../../../stock.xlsx"))

from src.main import app
from src.services.load_service import clear_store


@pytest.fixture(autouse=True)
def reset_store():
    clear_store()
    yield
    clear_store()


client = TestClient(app)


# ── helpers ───────────────────────────────────────────────────────────────────

def first_plan(capacity_tons=27):
    res = client.post("/web/api/v1/bin-packing", json={"truck_capacity_tons": capacity_tons})
    assert res.status_code == 200
    return res.json()[0]


def create_load(plan, destination="Porto de Santos", capacity_tons=27):
    return client.post("/web/api/v1/loads", json={
        "truck_capacity_tons": capacity_tons,
        "destination": destination,
        "items": [i["progressivo"] for i in plan["items"][:3]],
    })


# ── stock-labels ──────────────────────────────────────────────────────────────

class TestStockLabels:
    def test_returns_200_with_non_empty_array(self):
        res = client.get("/web/api/v1/stock-labels")
        assert res.status_code == 200
        assert isinstance(res.json(), list)
        assert len(res.json()) > 0

    def test_each_label_has_expected_fields(self):
        res = client.get("/web/api/v1/stock-labels")
        label = res.json()[0]
        for field in ["progressivo", "item_code", "volume_tons", "status", "warehouse_code"]:
            assert field in label, f"missing field: {field}"

    def test_volume_tons_is_metric_tons(self):
        res = client.get("/web/api/v1/stock-labels")
        assert all(l["volume_tons"] < 10 for l in res.json()), \
            "volume_tons looks like kg, not tons"

    def test_status_is_known_enum_value(self):
        valid = {
            "available_in_stock", "reserved", "in_transit_to_terminal",
            "available_in_terminal", "in_transit_to_client", "delivered", "idle", "damaged",
        }
        res = client.get("/web/api/v1/stock-labels")
        for label in res.json():
            assert label["status"] in valid, f"unknown status: {label['status']}"

    def test_exit_date_parsed_as_iso_date(self):
        res = client.get("/web/api/v1/stock-labels")
        labels_with_dates = [l for l in res.json() if l["exit_date"] is not None]
        assert len(labels_with_dates) > 0, "No labels have exit_date — date parsing may be broken"
        for label in labels_with_dates:
            assert len(label["exit_date"]) == 10, f"exit_date not YYYY-MM-DD: {label['exit_date']!r}"
            assert label["exit_date"][4] == "-" and label["exit_date"][7] == "-"

    def test_embarque_dash_not_a_valid_id(self):
        res = client.get("/web/api/v1/stock-labels")
        for label in res.json():
            assert label.get("embarque_id") != "-", \
                f"embarque_id='-' leaked through for {label['progressivo']}"


# ── bin-packing ───────────────────────────────────────────────────────────────

class TestBinPacking:
    def test_returns_422_when_capacity_missing(self):
        res = client.post("/web/api/v1/bin-packing", json={})
        assert res.status_code == 422

    def test_returns_load_plans_within_capacity(self):
        res = client.post("/web/api/v1/bin-packing", json={"truck_capacity_tons": 27})
        assert res.status_code == 200
        assert len(res.json()) > 0
        for plan in res.json():
            assert plan["totalTons"] <= 27 + 0.001
            assert len(plan["items"]) > 0

    def test_applies_customer_filter(self):
        full = client.post("/web/api/v1/bin-packing",
                           json={"truck_capacity_tons": 27}).json()
        customer = full[0]["items"][0]["customer"] if full else None
        if not customer:
            pytest.skip("No customer data in first plan")
        filtered = client.post("/web/api/v1/bin-packing", json={
            "truck_capacity_tons": 27,
            "filters": {"customer": customer},
        }).json()
        for plan in filtered:
            for item in plan["items"]:
                assert item["customer"] == customer

    def test_fewer_plans_with_low_max_iterations(self):
        full = client.post("/web/api/v1/bin-packing",
                           json={"truck_capacity_tons": 27, "max_iterations": 1000}).json()
        limited = client.post("/web/api/v1/bin-packing",
                              json={"truck_capacity_tons": 27, "max_iterations": 5}).json()
        assert len(limited) <= len(full)

    def test_each_plan_has_required_fields(self):
        res = client.post("/web/api/v1/bin-packing", json={"truck_capacity_tons": 27})
        for plan in res.json():
            for field in ["_id", "items", "totalTons", "totalPcs", "partial"]:
                assert field in plan, f"missing field: {field}"


# ── loads — create ────────────────────────────────────────────────────────────

class TestCreateLoad:
    def test_returns_422_when_required_fields_missing(self):
        res = client.post("/web/api/v1/loads", json={})
        assert res.status_code == 422

    def test_creates_load_with_status_pending(self):
        plan = first_plan()
        res = create_load(plan)
        assert res.status_code == 201
        body = res.json()
        assert body["status"] == "pending"
        assert body["id"]
        assert body["destination"] == "Porto de Santos"
        assert body["total_weight_tons"] > 0

    def test_total_weight_sums_resolved_items(self):
        plan = first_plan()
        picked = plan["items"][:2]
        expected = round(picked[0]["volume_tons"] + picked[1]["volume_tons"], 4)
        res = client.post("/web/api/v1/loads", json={
            "truck_capacity_tons": 27,
            "destination": "Test",
            "items": [i["progressivo"] for i in picked],
        })
        assert res.status_code == 201
        assert abs(res.json()["total_weight_tons"] - expected) < 0.001


# ── loads — list ──────────────────────────────────────────────────────────────

class TestListLoads:
    def test_returns_empty_array_when_no_loads(self):
        res = client.get("/web/api/v1/loads")
        assert res.status_code == 200
        assert res.json() == []

    def test_returns_created_loads(self):
        plan = first_plan()
        create_load(plan)
        res = client.get("/web/api/v1/loads")
        assert res.status_code == 200
        assert len(res.json()) == 1
        assert res.json()[0]["status"] == "pending"


# ── loads — items ─────────────────────────────────────────────────────────────

class TestLoadItems:
    def test_returns_404_for_unknown_id(self):
        res = client.get("/web/api/v1/loads/no-such-id/items")
        assert res.status_code == 404

    def test_returns_items_matching_submitted_progressivos(self):
        plan = first_plan()
        picked = plan["items"][:2]
        create_res = client.post("/web/api/v1/loads", json={
            "truck_capacity_tons": 27,
            "destination": "Test",
            "items": [i["progressivo"] for i in picked],
        })
        load_id = create_res.json()["id"]
        res = client.get(f"/web/api/v1/loads/{load_id}/items")
        assert res.status_code == 200
        assert len(res.json()) == len(picked)
        returned_ids = {i["progressivo"] for i in res.json()}
        for p in picked:
            assert p["progressivo"] in returned_ids


# ── loads — status transition ─────────────────────────────────────────────────

class TestLoadStatusTransition:
    def test_returns_404_for_unknown_id(self):
        res = client.patch("/web/api/v1/loads/no-such-id/status")
        assert res.status_code == 404

    def test_pending_to_in_transit(self):
        plan = first_plan()
        load_id = create_load(plan).json()["id"]
        res = client.patch(f"/web/api/v1/loads/{load_id}/status")
        assert res.status_code == 200
        assert res.json()["status"] == "in_transit"
        assert res.json()["in_transit_at"]
        assert res.json()["dispatched_at"] is None

    def test_in_transit_to_dispatched(self):
        plan = first_plan()
        load_id = create_load(plan).json()["id"]
        client.patch(f"/web/api/v1/loads/{load_id}/status")
        res = client.patch(f"/web/api/v1/loads/{load_id}/status")
        assert res.json()["status"] == "dispatched"
        assert res.json()["dispatched_at"]

    def test_dispatched_to_delivered(self):
        plan = first_plan()
        load_id = create_load(plan).json()["id"]
        for _ in range(2):
            client.patch(f"/web/api/v1/loads/{load_id}/status")
        res = client.patch(f"/web/api/v1/loads/{load_id}/status")
        assert res.json()["status"] == "delivered"
        assert res.json()["delivered_at"]

    def test_returns_422_when_no_further_transition(self):
        plan = first_plan()
        load_id = create_load(plan).json()["id"]
        for _ in range(3):
            client.patch(f"/web/api/v1/loads/{load_id}/status")
        res = client.patch(f"/web/api/v1/loads/{load_id}/status")
        assert res.status_code == 422
