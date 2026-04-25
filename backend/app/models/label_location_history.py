import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class LabelLocationHistory(Base):
    __tablename__ = "label_location_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    progressivo: Mapped[str] = mapped_column(String(64), ForeignKey("stock_labels.progressivo"), nullable=False)
    from_location_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("locations.id"))
    to_location_id: Mapped[str] = mapped_column(String(36), ForeignKey("locations.id"), nullable=False)
    moved_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    stock_label: Mapped["StockLabel"] = relationship(back_populates="location_history")  # noqa: F821
