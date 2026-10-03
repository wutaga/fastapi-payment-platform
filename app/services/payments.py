from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Payment


def payment_matches_create_data(
    existing_payment: Payment,
    amount_kopecks: int,
    description: str | None,
) -> bool:
    return (
        existing_payment.amount_kopecks == amount_kopecks
        and existing_payment.description == description
    )


def create_payment_in_session(
    db: Session,
    organization_id: int,
    api_key_id: int,
    amount_kopecks: int,
    merchant_order_id: str,
    description: str | None,
) -> Payment:
    payment = Payment(
        organization_id=organization_id,
        api_key_id=api_key_id,
        amount_kopecks=amount_kopecks,
        merchant_order_id=merchant_order_id,
        description=description,
    )
    db.add(payment)
    return payment


def find_payment_by_merchant_order_id(
    db: Session,
    organization_id: int,
    merchant_order_id: str,
) -> Payment | None:
    stmt = select(Payment).where(
        Payment.organization_id == organization_id,
        Payment.merchant_order_id == merchant_order_id,
    )
    existing_payment = db.execute(stmt).scalar_one_or_none()
    return existing_payment


def find_payment_by_id(
    db: Session,
    organization_id: int,
    payment_id: int,
) -> Payment | None:
    stmt = select(Payment).where(
        Payment.id == payment_id,
        Payment.organization_id == organization_id,
    )
    payment = db.execute(stmt).scalar_one_or_none()
    return payment


def find_payments_by_organization(
    db: Session,
    organization_id: int,
    limit: int,
    offset: int,
    status: str | None,
) -> list[Payment]:
    stmt = select(Payment).where(Payment.organization_id == organization_id)
    if status is not None:
        stmt = stmt.where(Payment.status == status)
    stmt = stmt.order_by(Payment.id.desc()).limit(limit).offset(offset)

    payments = db.execute(stmt).scalars().all()
    return payments
