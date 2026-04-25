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


class PackingFilters(BaseModel):
    country: str | None = None
    order_condition: str | None = None
