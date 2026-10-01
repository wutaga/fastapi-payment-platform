from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.api_key import ApiKey
    from app.models.organization import Organization


class Payment(Base):
    __tablename__ = "payments"

    __table_args__ = (
        CheckConstraint(
            "amount_kopecks >= 5000 AND amount_kopecks <= 100000000",
            name="check_payments_amount_kopecks_range",
        ),
        UniqueConstraint(
            "organization_id",
            "merchant_order_id",
            name="unique_payments_organization_id_merchant_order_id",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    api_key_id: Mapped[int] = mapped_column(ForeignKey("api_keys.id"))
    amount_kopecks: Mapped[int]
    status: Mapped[str] = mapped_column(String(32), default="pending")
    merchant_order_id: Mapped[str] = mapped_column(String(128))
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
    )
    processed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    organization: Mapped[Organization] = relationship(back_populates="payments")
    api_key: Mapped[ApiKey] = relationship(back_populates="payments")
