from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from ...data.xlsx_loader import load_labels
from ...services.ffd import ffd

router = APIRouter()


class BinPackingFilters(BaseModel):
    warehouse_code: Optional[str] = None
    customer: Optional[str] = None


class BinPackingRequest(BaseModel):
    truck_capacity_tons: float
    filters: Optional[BinPackingFilters] = None
    max_iterations: int = 1000


@router.post("/")
def run_bin_packing(body: BinPackingRequest):
    if body.truck_capacity_tons <= 0:
        raise HTTPException(status_code=422, detail="truck_capacity_tons must be positive")

    labels = [l for l in load_labels() if l["status"] in ("available_in_stock", "reserved")]

    if body.filters:
        if body.filters.warehouse_code:
            labels = [l for l in labels if l["warehouse_code"] == body.filters.warehouse_code]
        if body.filters.customer:
            labels = [l for l in labels if l["customer"] == body.filters.customer]

    return ffd(labels, body.truck_capacity_tons, body.max_iterations)
