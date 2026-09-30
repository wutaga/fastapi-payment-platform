from datetime import datetime

from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    api_key_id: Mapped[int] = mapped_column(ForeignKey("api_keys.id"))
    amount_kopecks: Mapped[int]
    status: Mapped[str] = mapped_column(default="pending")
    merchant_order_id: Mapped[str]
    description: Mapped[str | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
    )
    processed_at: Mapped[datetime | None] = mapped_column(nullable=True)