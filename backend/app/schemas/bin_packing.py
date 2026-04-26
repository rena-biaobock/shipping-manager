from datetime import date

from pydantic import BaseModel


class TruckInput(BaseModel):
    id: str
    max_weight_tons: float


class LabelInput(BaseModel):
    progressivo: str
    volume_tons: float
    market_type: str
    country: str
    order_condition: str
    exit_date: date | None = None


class PackingFilters(BaseModel):
    country: str | None = None
    order_condition: str | None = None
    exit_date_from: date | None = None
    exit_date_to: date | None = None
