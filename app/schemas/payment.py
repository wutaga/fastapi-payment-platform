from datetime import datetime

from pydantic import BaseModel, Field


class PaymentCreate(BaseModel):
    merchant_order_id: str = Field(min_length=1, max_length=128)
    amount_kopecks: int = Field(ge=5_000, le=100_000_000)
    description: str | None = Field(default=None, max_length=500)


class PaymentResponse(BaseModel):
    id: int
    merchant_order_id: str
    amount_kopecks: int
    status: str
    description: str | None
    created_at: datetime
    updated_at: datetime
    processed_at: datetime | None