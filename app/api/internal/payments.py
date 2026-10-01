from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.models import Payment
from app.schemas.payment import PaymentProcess, PaymentResponse

router = APIRouter(prefix="/payments", tags=["internal-payments"])


@router.post("/{payment_id}/process", response_model=PaymentResponse)
def process_payment_test(
    payment_id: int,
    payload: PaymentProcess,
    db: Session = Depends(get_db),
) -> PaymentResponse:
    stmt = select(Payment).where(
        Payment.id == payment_id,
    )
    payment = db.execute(stmt).scalar_one_or_none()
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")

    if payment.status != "pending":
        raise HTTPException(status_code=409, detail="Payment is already processed")

    payment.status = payload.status
    payment.processed_at = datetime.now(UTC)
    db.commit()
    db.refresh(payment)
    return payment
