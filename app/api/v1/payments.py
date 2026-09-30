from datetime import datetime, UTC

from fastapi import APIRouter, Depends

from app.api.dependencies import get_api_key
from app.models import ApiKey
from app.schemas.payment import PaymentCreate, PaymentResponse


router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("", response_model=PaymentResponse)
def create_payment(
    payload: PaymentCreate,
    current_api_key: ApiKey = Depends(get_api_key),
) -> PaymentResponse:
    _ = current_api_key
    now = datetime.now(UTC)
    return {
        "id": 1,
        "merchant_order_id": payload.merchant_order_id,
        "amount_kopecks": payload.amount_kopecks,
        "status": "pending",
        "description": payload.description,
        "created_at": now,
        "updated_at": now,
        "processed_at": None,
    }