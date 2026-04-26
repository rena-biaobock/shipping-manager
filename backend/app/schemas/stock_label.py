from decimal import Decimal

from pydantic import BaseModel


class StockLabelRead(BaseModel):
    progressivo: str
    item_code: str
    description: str
    customer_item_ref: str | None = None
    actual_length_m: Decimal | None = None
    market_type: str
    volume_tons: Decimal
    piece_count: int
    status: str
    order_number: str | None = None
    order_condition: str | None = None
    country: str | None = None
    exit_date: str | None = None
    embarque_id: str | None = None
    avg_days_idle: int | None = None
    is_standard_bundle: bool | None = None
    location_id: str | None = None

    model_config = {"from_attributes": True}


class StockLabelStatusUpdate(BaseModel):
    new_status: str


class StockLabelLocationUpdate(BaseModel):
    location_id: str
