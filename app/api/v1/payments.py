from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_api_key
from app.db.dependencies import get_db
from app.models import ApiKey
from app.schemas.payment import PaymentCreate, PaymentResponse
from app.services.payments import (
    create_payment_in_session,
    find_payment_by_id,
    find_payment_by_merchant_order_id,
    find_payments_by_organization,
    payment_matches_create_data,
)

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("", response_model=PaymentResponse)
def create_payment(
    payload: PaymentCreate,
    current_api_key: ApiKey = Depends(get_api_key),
    db: Session = Depends(get_db),
) -> PaymentResponse:
    existing_payment = find_payment_by_merchant_order_id(
        db=db,
        organization_id=current_api_key.organization_id,
        merchant_order_id=payload.merchant_order_id,
    )
    if existing_payment is not None:
        same_payment_data = payment_matches_create_data(
            existing_payment,
            amount_kopecks=payload.amount_kopecks,
            description=payload.description,
        )
        if not same_payment_data:
            raise HTTPException(
                status_code=409,
                detail="Payment already exists with different data",
            )
        return existing_payment
    payment = create_payment_in_session(
        db=db,
        organization_id=current_api_key.organization_id,
        api_key_id=current_api_key.id,
        amount_kopecks=payload.amount_kopecks,
        merchant_order_id=payload.merchant_order_id,
        description=payload.description,
    )
    db.commit()
    db.refresh(payment)
    return payment


@router.get("", response_model=list[PaymentResponse])
def get_payments_by_organization(
    current_api_key: ApiKey = Depends(get_api_key),
    db: Session = Depends(get_db),
) -> list[PaymentResponse]:
    payments = find_payments_by_organization(
        db=db,
        organization_id=current_api_key.organization_id,
    )
    return payments


@router.get("/by-order/{merchant_order_id}", response_model=PaymentResponse)
def get_payment_by_merchant_order_id(
    merchant_order_id: str,
    current_api_key: ApiKey = Depends(get_api_key),
    db: Session = Depends(get_db),
) -> PaymentResponse:
    payment = find_payment_by_merchant_order_id(
        db=db,
        organization_id=current_api_key.organization_id,
        merchant_order_id=merchant_order_id,
    )
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(
    payment_id: int,
    current_api_key: ApiKey = Depends(get_api_key),
    db: Session = Depends(get_db),
) -> PaymentResponse:
    payment = find_payment_by_id(
        db=db,
        organization_id=current_api_key.organization_id,
        payment_id=payment_id,
    )
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment