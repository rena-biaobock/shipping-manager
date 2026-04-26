import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class LoadItem(Base):
    __tablename__ = "load_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    shipment_id: Mapped[str] = mapped_column(String(36), ForeignKey("shipments.id"), nullable=False)
    stock_label_id: Mapped[str] = mapped_column(String(64), ForeignKey("stock_labels.progressivo"), nullable=False)

    shipment: Mapped["Shipment"] = relationship(back_populates="load_items")  # noqa: F821
    stock_label: Mapped["StockLabel"] = relationship()  # noqa: F821
