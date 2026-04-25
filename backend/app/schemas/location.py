from pydantic import BaseModel


class LocationCreate(BaseModel):
    name: str


class LocationRead(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    name: str
    active: bool
