import uuid
from datetime import datetime, timezone

_TRANSITIONS = {
    "pending": "in_transit",
    "in_transit": "dispatched",
    "dispatched": "delivered",
}

_store: dict[str, dict] = {}


def get_all_loads() -> list[dict]:
    return [{k: v for k, v in load.items() if k != "items"} for load in _store.values()]


def get_load_items(load_id: str) -> list[dict] | None:
    load = _store.get(load_id)
    return None if load is None else load["items"]


def create_load(truck_capacity_tons: float, destination: str, items: list[dict]) -> dict:
    total_weight_tons = round(sum(i["volume_tons"] for i in items), 4)
    load_id = str(uuid.uuid4())
    load = {
        "id": load_id,
        "truck_capacity_tons": truck_capacity_tons,
        "destination": destination,
        "status": "pending",
        "total_weight_tons": total_weight_tons,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "in_transit_at": None,
        "dispatched_at": None,
        "delivered_at": None,
        "items": items,
    }
    _store[load_id] = load
    return {k: v for k, v in load.items() if k != "items"} | {"item_count": len(items)}


def advance_status(load_id: str) -> dict | None:
    load = _store.get(load_id)
    if load is None:
        return None

    next_status = _TRANSITIONS.get(load["status"])
    if next_status is None:
        raise ValueError(f"No valid transition from '{load['status']}'")

    load["status"] = next_status
    now = datetime.now(timezone.utc).isoformat()
    if next_status == "in_transit":
        load["in_transit_at"] = now
    elif next_status == "dispatched":
        load["dispatched_at"] = now
    elif next_status == "delivered":
        load["delivered_at"] = now

    return {k: v for k, v in load.items() if k != "items"}


def clear_store() -> None:
    _store.clear()
