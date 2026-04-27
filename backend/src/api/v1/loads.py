from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from ...services.load_service import (
    get_all_loads, get_load_items, create_load, advance_status,
)
from ...data.xlsx_loader import load_labels

router = APIRouter()


class CreateLoadRequest(BaseModel):
    truck_capacity_tons: float
    destination: str
    items: list[str]
    truck_plate: Optional[str] = None


@router.get("/")
def list_loads():
    return get_all_loads()


@router.get("/{load_id}/items")
def get_items(load_id: str):
    items = get_load_items(load_id)
    if items is None:
        raise HTTPException(status_code=404, detail="Load not found")
    return items


@router.post("/", status_code=201)
def create(body: CreateLoadRequest):
    label_map = {l["progressivo"]: l for l in load_labels()}
    resolved = [label_map[p] for p in body.items if p in label_map]
    if not resolved:
        raise HTTPException(status_code=400, detail="No valid items found")
    return create_load(body.truck_capacity_tons, body.destination, resolved)


@router.patch("/{load_id}/status")
def transition_status(load_id: str):
    try:
        result = advance_status(load_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    if result is None:
        raise HTTPException(status_code=404, detail="Load not found")
    return result
