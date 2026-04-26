import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Shipment(Base):
    __tablename__ = "shipments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    truck_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("trucks.id"))
    order_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("orders.id"))
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    destination: Mapped[str | None] = mapped_column(String(255))
    customer: Mapped[str | None] = mapped_column(String(255))
    country: Mapped[str | None] = mapped_column(String(64))
    market_type: Mapped[str | None] = mapped_column(String(2))
    notes: Mapped[str | None] = mapped_column(Text)
    total_weight_tons: Mapped[Decimal | None] = mapped_column(Numeric(10, 3))
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime)
    dispatched_at: Mapped[datetime | None] = mapped_column(DateTime)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime)

    truck: Mapped["Truck | None"] = relationship(back_populates="shipments")  # noqa: F821
    order: Mapped["Order | None"] = relationship(back_populates="shipments")  # noqa: F821
    load_items: Mapped[list["LoadItem"]] = relationship(back_populates="shipment")  # noqa: F821
