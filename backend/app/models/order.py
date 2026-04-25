import uuid
from datetime import date

from sqlalchemy import Date, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_number: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    client_order_ref: Mapped[str | None] = mapped_column(String(64))
    customer: Mapped[str | None] = mapped_column(String(255))
    country: Mapped[str | None] = mapped_column(String(64))
    market_type: Mapped[str] = mapped_column(String(2), nullable=False)
    condition: Mapped[str] = mapped_column(String(32), nullable=False)
    exit_date: Mapped[date | None] = mapped_column(Date)

    shipments: Mapped[list["Shipment"]] = relationship(back_populates="order")  # noqa: F821
