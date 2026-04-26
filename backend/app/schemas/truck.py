from decimal import Decimal

from pydantic import BaseModel


class TruckCreate(BaseModel):
    name: str
    plate: str | None = None
    max_weight_tons: Decimal


class TruckRead(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    name: str
    plate: str | None
    max_weight_tons: Decimal
    active: bool
