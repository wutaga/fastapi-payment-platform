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