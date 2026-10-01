import httpx
import pytest
from fastapi.testclient import TestClient

from app.models import ApiKey


@pytest.mark.parametrize("target_status", ["succeeded", "failed"])
def test_process_payment_to_final_status(
    client: TestClient,
    api_key: ApiKey,
    target_status: str,
):
    _ = api_key

    create_response: httpx.Response = client.post(
        "/api/v1/payments",
        headers={"Authorization": "Bearer test_api_key"},
        json={
            "merchant_order_id": f"order_process_{target_status}",
            "amount_kopecks": 5000,
            "description": "test",
        },
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
):
    _ = api_key

    create_response: httpx.Response = client.post(
        "/api/v1/payments",
        headers={"Authorization": "Bearer test_api_key"},
        json={
            "merchant_order_id": "order_1",
            "amount_kopecks": 15000,
            "description": "test",
        },
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
