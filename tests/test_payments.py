import httpx
import pytest
from fastapi.testclient import TestClient

from app.models import ApiKey


def test_create_payment_success(client: TestClient, api_key):
    _ = api_key
    response = client.post(
        "/api/v1/payments",
        headers={"Authorization": "Bearer test_api_key"},
        json={
            "merchant_order_id": "order_test_1",
            "amount_kopecks": 150000,
            "description": "test",
        },
    )

    body = response.json()

    assert response.status_code == 200
    assert body["merchant_order_id"] == "order_test_1"
    assert body["amount_kopecks"] == 150000
    assert body["status"] == "pending"
    assert body["description"] == "test"
    assert body["processed_at"] is None
    assert isinstance(body["id"], int)


def test_create_payment_invalid_api_key(client: TestClient, api_key):
    _ = api_key
    response: httpx.Response = client.post(
        "/api/v1/payments",
        headers={"Authorization": "Bearer wrong_key"},
        json={
            "merchant_order_id": "order_test_1",
            "amount_kopecks": 150000,
            "description": "test",
        },
    )

    body = response.json()

    assert response.status_code == 401
    assert body["detail"] == "Invalid API key"


def test_create_payment_without_authorization(client: TestClient):
    response: httpx.Response = client.post(
        "/api/v1/payments",
        json={
            "merchant_order_id": "order_test_1",
            "amount_kopecks": 150000,
            "description": "test",
        },
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.parametrize("amount_kopecks", [4_999, 100_000_001])
def test_create_payment_invalid_amount(client, api_key, amount_kopecks: int):
    _ = api_key

    response = client.post(
        "/api/v1/payments",
        headers={"Authorization": "Bearer test_api_key"},
        json={
            "merchant_order_id": "order_invalid_amount",
            "amount_kopecks": amount_kopecks,
            "description": "test",
        },
    )

    assert response.status_code == 422


def test_create_payment_duplicate_same_data_returns_existing_payment(
    client: TestClient,
    api_key: ApiKey,
):
    _ = api_key
    response_1 = client.post(
        "/api/v1/payments",
        headers={"Authorization": "Bearer test_api_key"},
        json={
            "merchant_order_id": "order_X1_Y2",
            "amount_kopecks": 5000,
            "description": "test",
        },
    )
    payment_id_1 = response_1.json()["id"]
    response_2 = client.post(
        "/api/v1/payments",
        headers={"Authorization": "Bearer test_api_key"},
        json={
            "merchant_order_id": "order_X1_Y2",
            "amount_kopecks": 5000,
            "description": "test",
        },
    )
    payment_id_2 = response_2.json()["id"]

    assert response_1.status_code == 200
    assert response_2.status_code == 200
    assert payment_id_1 == payment_id_2


def test_create_payment_duplicate_same_merchant_order_id_but_different_amount(
    client: TestClient,
    api_key: ApiKey,
):
    _ = api_key

    response_1: httpx.Response = client.post(
        "/api/v1/payments",
        headers={"Authorization": "Bearer test_api_key"},
        json={
            "merchant_order_id": "order_X1_Y2",
            "amount_kopecks": 5000,
            "description": "test",
        },
    )

    response_2: httpx.Response = client.post(
        "/api/v1/payments",
        headers={"Authorization": "Bearer test_api_key"},
        json={
            "merchant_order_id": "order_X1_Y2",
            "amount_kopecks": 45000,
            "description": "test",
        },
    )

    assert response_1.status_code == 200
    assert response_2.status_code == 409
    assert response_2.json() == {"detail": "Payment already exists with different data"}


def test_get_payment_by_id_success(client: TestClient, api_key: ApiKey):
    _ = api_key

    create_response: httpx.Response = client.post(
        "/api/v1/payments",
        headers={"Authorization": "Bearer test_api_key"},
        json={
            "merchant_order_id": "order_get_by_id",
            "amount_kopecks": 150000,
            "description": "get by id test",
        },
    )

    payment_id = create_response.json()["id"]

    get_response: httpx.Response = client.get(
        f"/api/v1/payments/{payment_id}",
        headers={"Authorization": "Bearer test_api_key"},
    )

    body = get_response.json()

    assert create_response.status_code == 200
    assert get_response.status_code == 200
    assert body["id"] == payment_id
    assert body["merchant_order_id"] == "order_get_by_id"
    assert body["amount_kopecks"] == 150000
    assert body["status"] == "pending"
    assert body["description"] == "get by id test"


def test_get_payment_by_id_not_found(client: TestClient, api_key: ApiKey):
    _ = api_key

    response: httpx.Response = client.get(
        "/api/v1/payments/999999",
        headers={"Authorization": "Bearer test_api_key"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Payment not found"}


def test_get_payment_by_merchant_order_id_success(client: TestClient, api_key: ApiKey):
    _ = api_key

    merchant_order_id = "12345"

    create_response: httpx.Response = client.post(
        "/api/v1/payments",
        headers={"Authorization": "Bearer test_api_key"},
        json={
            "merchant_order_id": merchant_order_id,
            "amount_kopecks": 1600000,
            "description": "get by merchant order id",
        },
    )

    response: httpx.Response = client.get(
        f"/api/v1/payments/by-order/{merchant_order_id}",
        headers={"Authorization": "Bearer test_api_key"},
    )

    body = response.json()

    assert create_response.status_code == 200
    assert response.status_code == 200
    assert body["id"] == create_response.json()["id"]
    assert body["merchant_order_id"] == "12345"
    assert body["amount_kopecks"] == 1600000
    assert body["status"] == "pending"
    assert body["description"] == "get by merchant order id"


def test_get_payment_by_merchant_order_id_not_found(client: TestClient, api_key: ApiKey):
    _ = api_key
    response: httpx.Response = client.get(
        "/api/v1/payments/by-order/12345",
        headers={"Authorization": "Bearer test_api_key"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Payment not found"}


def test_get_payment_by_id_without_authorization(
    client: TestClient,
    api_key: ApiKey,
):
    _ = api_key

    create_response: httpx.Response = client.post(
        "/api/v1/payments",
        headers={"Authorization": "Bearer test_api_key"},
        json={
            "merchant_order_id": "123DCX-3241SS",
            "amount_kopecks": 100_000_000,
            "description": "test_payment",
        },
    )
    created_response_body = create_response.json()
    payment_id = created_response_body["id"]

    get_response: httpx.Response = client.get(
        f"/api/v1/payments/{payment_id}",
    )

    assert create_response.status_code == 200
    assert get_response.status_code == 401
    assert get_response.json() == {"detail": "Not authenticated"}

def test_get_payment_by_order_id_without_authorization(
    client: TestClient,
    api_key: ApiKey,
):
    _ = api_key
    order_id = "123DCX-3241SS-0001"

    create_response: httpx.Response = client.post(
        "/api/v1/payments",
        headers={"Authorization": "Bearer test_api_key"},
        json={
            "merchant_order_id": order_id,
            "amount_kopecks": 99_000_000,
            "description": "test_payment",
        },
    )
    get_response: httpx.Response = client.get(
        f"/api/v1/payments/by-order/{order_id}",
    )

    assert create_response.status_code == 200
    assert get_response.status_code == 401
    assert get_response.json() == {"detail": "Not authenticated"}

