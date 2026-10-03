import httpx
import pytest
from fastapi.testclient import TestClient

from app.models import ApiKey

# Process payment POST /internal/payments/{payment_id}/process


@pytest.mark.parametrize("target_status", ["succeeded", "failed"])
def test_process_payment_to_final_status(
    client: TestClient,
    api_key: ApiKey,
    target_status: str,
    create_payment,
):
    _ = api_key

    create_response = create_payment(
        merchant_order_id=f"order_process_{target_status}",
        amount_kopecks=5000,
        description="test",
    )

    created_payment = create_response.json()
    payment_id = created_payment["id"]

    process_response: httpx.Response = client.post(
        f"/internal/payments/{payment_id}/process",
        json={"status": target_status},
    )
    processed_payment = process_response.json()

    assert create_response.status_code == 200
    assert created_payment["status"] == "pending"
    assert created_payment["processed_at"] is None

    assert process_response.status_code == 200
    assert processed_payment["id"] == created_payment["id"]
    assert processed_payment["status"] == target_status
    assert processed_payment["processed_at"] is not None


def test_process_payment_already_processed_returns_409(
    client: TestClient,
    api_key: ApiKey,
    create_payment,
):
    _ = api_key

    create_response = create_payment(
        merchant_order_id="order_already_processed",
        amount_kopecks=15000,
        description="test",
    )

    created_payment = create_response.json()
    payment_id = created_payment["id"]

    process_response: httpx.Response = client.post(
        f"/internal/payments/{payment_id}/process",
        json={"status": "succeeded"},
    )
    processed_response = process_response.json()

    second_process_response: httpx.Response = client.post(
        f"/internal/payments/{payment_id}/process",
        json={"status": "failed"},
    )

    assert create_response.status_code == 200
    assert created_payment["status"] == "pending"
    assert created_payment["processed_at"] is None

    assert process_response.status_code == 200
    assert processed_response["status"] == "succeeded"

    assert second_process_response.status_code == 409
    assert second_process_response.json() == {"detail": "Payment is already processed"}


def test_process_payment_unknown_status_returns_422(
    client: TestClient,
    api_key: ApiKey,
    create_payment,
):
    _ = api_key

    create_response = create_payment(
        merchant_order_id="order_process_unknown",
        amount_kopecks=5000,
        description="test_unknown_status",
    )

    created_payment = create_response.json()
    payment_id = created_payment["id"]

    process_response: httpx.Response = client.post(
        f"/internal/payments/{payment_id}/process",
        json={"status": "unknown"},
    )
    processed_payment = process_response.json()

    assert create_response.status_code == 200
    assert created_payment["status"] == "pending"

    assert process_response.status_code == 422
    assert processed_payment["detail"][0]["loc"] == ["body", "status"]
    assert processed_payment["detail"][0]["type"] == "literal_error"


def test_process_payment_nonexistent_payment_returns_404(client: TestClient):
    process_response: httpx.Response = client.post(
        "/internal/payments/999999/process",
        json={"status": "succeeded"},
    )
    processed_payment = process_response.json()

    assert process_response.status_code == 404
    assert processed_payment == {"detail": "Payment not found"}
