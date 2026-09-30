from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_api_key
from app.db.dependencies import get_db
from app.models import ApiKey, Payment
from app.schemas.payment import PaymentCreate, PaymentResponse


router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("", response_model=PaymentResponse)
def create_payment(
    payload: PaymentCreate,
    current_api_key: ApiKey = Depends(get_api_key),
    db: Session = Depends(get_db),
) -> PaymentResponse:
    stmt = select(Payment).where(
        Payment.organization_id == current_api_key.organization_id,
        Payment.merchant_order_id == payload.merchant_order_id,
    )
    existing_payment = db.execute(stmt).scalar_one_or_none()
    if existing_payment is not None:
        same_payment_data = (
            existing_payment.amount_kopecks == payload.amount_kopecks
            and existing_payment.description == payload.description
        )
        if not same_payment_data:
            raise HTTPException(
                status_code=409,
                detail="Payment already exists with different data",
            )
        return existing_payment
    payment = Payment(
        organization_id=current_api_key.organization_id,
        api_key_id=current_api_key.id,
        amount_kopecks=payload.amount_kopecks,
        merchant_order_id=payload.merchant_order_id,
        description=payload.description,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment
