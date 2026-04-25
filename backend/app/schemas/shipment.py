from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class ShipmentCreate(BaseModel):
    truck_id: str
    destination: str | None = None
    customer: str | None = None
    country: str | None = None
    market_type: str | None = None
    notes: str | None = None
    scheduled_at: datetime | None = None


class ShipmentRead(BaseModel):
    id: str
    truck_id: str | None = None
    order_id: str | None = None
    status: str
    destination: str | None = None
    customer: str | None = None
    country: str | None = None
    market_type: str | None = None
    notes: str | None = None
    total_weight_tons: Decimal | None = None
    scheduled_at: datetime | None = None
    dispatched_at: datetime | None = None
    delivered_at: datetime | None = None

    model_config = {"from_attributes": True}


class ShipmentStatusUpdate(BaseModel):
    new_status: str


class ShipmentLabelsAdd(BaseModel):
    progressivos: list[str]


class LoadItemRead(BaseModel):
    id: str
    shipment_id: str
    stock_label_id: str

    model_config = {"from_attributes": True}
