import uuid
from decimal import Decimal

from sqlalchemy import Boolean, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Truck(Base):
    __tablename__ = "trucks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    plate: Mapped[str | None] = mapped_column(String(32), unique=True)
    max_weight_tons: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    shipments: Mapped[list["Shipment"]] = relationship(back_populates="truck")  # noqa: F821
