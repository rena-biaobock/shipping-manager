import pytest
from src.services.load_service import (
    create_load, advance_status, get_all_loads, get_load_items, clear_store,
)

SAMPLE_ITEMS = [
    {"progressivo": "P001", "volume_tons": 5.0, "piece_count": 10, "item_code": "ITM1",
     "description": "Pipe A", "customer": "ACME", "status": "available_in_stock"},
    {"progressivo": "P002", "volume_tons": 3.0, "piece_count": 6, "item_code": "ITM2",
     "description": "Pipe B", "customer": "ACME", "status": "reserved"},
]


@pytest.fixture(autouse=True)
def reset_store():
    clear_store()
    yield
    clear_store()


def test_create_load_returns_pending_status():
    result = create_load(27.0, "Porto de Santos", SAMPLE_ITEMS)
    assert result["status"] == "pending"


def test_create_load_has_id_and_destination():
    result = create_load(27.0, "Porto de Santos", SAMPLE_ITEMS)
    assert result["id"]
    assert result["destination"] == "Porto de Santos"


def test_create_load_sums_weight_correctly():
    result = create_load(27.0, "Destination", SAMPLE_ITEMS)
    expected = round(5.0 + 3.0, 4)
    assert abs(result["total_weight_tons"] - expected) < 0.001


def test_create_load_sets_item_count():
    result = create_load(27.0, "Destination", SAMPLE_ITEMS)
    assert result["item_count"] == len(SAMPLE_ITEMS)


def test_get_all_loads_empty_initially():
    assert get_all_loads() == []


def test_get_all_loads_returns_created_loads():
    create_load(27.0, "Dest", SAMPLE_ITEMS)
    loads = get_all_loads()
    assert len(loads) == 1
    assert loads[0]["status"] == "pending"


def test_get_all_loads_does_not_include_items():
    create_load(27.0, "Dest", SAMPLE_ITEMS)
    loads = get_all_loads()
    assert "items" not in loads[0]


def test_get_load_items_returns_items():
    result = create_load(27.0, "Dest", SAMPLE_ITEMS)
    items = get_load_items(result["id"])
    assert items is not None
    assert len(items) == len(SAMPLE_ITEMS)


def test_get_load_items_returns_none_for_unknown_id():
    assert get_load_items("no-such-id") is None


def test_advance_status_pending_to_in_transit():
    result = create_load(27.0, "Dest", SAMPLE_ITEMS)
    advanced = advance_status(result["id"])
    assert advanced["status"] == "in_transit"
    assert advanced["dispatched_at"] is not None


def test_advance_status_in_transit_to_dispatched():
    result = create_load(27.0, "Dest", SAMPLE_ITEMS)
    advance_status(result["id"])
    advanced = advance_status(result["id"])
    assert advanced["status"] == "dispatched"


def test_advance_status_dispatched_to_delivered():
    result = create_load(27.0, "Dest", SAMPLE_ITEMS)
    advance_status(result["id"])
    advance_status(result["id"])
    advanced = advance_status(result["id"])
    assert advanced["status"] == "delivered"
    assert advanced["delivered_at"] is not None


def test_advance_status_raises_on_terminal_state():
    result = create_load(27.0, "Dest", SAMPLE_ITEMS)
    for _ in range(3):
        advance_status(result["id"])
    with pytest.raises(ValueError, match="No valid transition"):
        advance_status(result["id"])


def test_advance_status_returns_none_for_unknown_id():
    assert advance_status("no-such-id") is None
