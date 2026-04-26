from decimal import Decimal

from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class StockLabel(Base):
    __tablename__ = "stock_labels"

    progressivo: Mapped[str] = mapped_column(String(64), primary_key=True)
    item_code: Mapped[str] = mapped_column(String(32), nullable=False)
    description: Mapped[str] = mapped_column(String(512), nullable=False)
    customer_item_ref: Mapped[str | None] = mapped_column(String(128))
    actual_length_m: Mapped[Decimal | None] = mapped_column(Numeric(8, 3))
    market_type: Mapped[str] = mapped_column(String(2), nullable=False)
    volume_tons: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    piece_count: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="available")
    order_number: Mapped[str | None] = mapped_column(String(64))
    order_condition: Mapped[str | None] = mapped_column(String(32))
    country: Mapped[str | None] = mapped_column(String(64))
    exit_date: Mapped[str | None] = mapped_column(String(10))  # ISO date string
    embarque_id: Mapped[str | None] = mapped_column(String(32))
    avg_days_idle: Mapped[int | None] = mapped_column(Integer)
    is_standard_bundle: Mapped[bool | None] = mapped_column()

    location_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("locations.id"))
    location: Mapped["Location | None"] = relationship(back_populates="stock_labels")  # noqa: F821

    location_history: Mapped[list["LabelLocationHistory"]] = relationship(back_populates="stock_label")  # noqa: F821
