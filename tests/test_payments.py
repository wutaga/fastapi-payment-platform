import httpx
import pytest
from fastapi.testclient import TestClient

from app.models import ApiKey

# Create payment POST /api/v1/payments


def test_create_payment_success(
    api_key,
    create_payment,
):
    _ = api_key
    merchant_order_id = "order_test_1"

    response = create_payment(
        merchant_order_id=merchant_order_id,
        amount_kopecks=150000,
        description="test",
    )

    body = response.json()

    assert response.status_code == 200
    assert body["merchant_order_id"] == merchant_order_id
    assert body["amount_kopecks"] == 150000
    assert body["status"] == "pending"
    assert body["description"] == "test"
    assert body["processed_at"] is None
    assert isinstance(body["id"], int)


def test_create_payment_without_description_success(
    client: TestClient,
    api_key,
):
    _ = api_key

    response: httpx.Response = client.post(
        "/api/v1/payments",
        headers={"Authorization": "Bearer test_api_key"},
        json={
            "merchant_order_id": "create_payment_without_description",
            "amount_kopecks": 5001,
        },
    )

    response_body = response.json()

    assert response.status_code == 200
    assert response_body["merchant_order_id"] == "create_payment_without_description"
    assert response_body["amount_kopecks"] == 5001
    assert response_body["status"] == "pending"
    assert response_body["description"] is None
    assert response_body["processed_at"] is None


def test_create_payment_with_null_description_success(
    client: TestClient,
    api_key,
):
    _ = api_key

    response: httpx.Response = client.post(
        "/api/v1/payments",
        headers={"Authorization": "Bearer test_api_key"},
        json={
            "merchant_order_id": "with_null_description",
            "amount_kopecks": 99_999_999,
            "description": None,
        },
    )

    response_body = response.json()

    assert response.status_code == 200
    assert response_body["merchant_order_id"] == "with_null_description"
    assert response_body["amount_kopecks"] == 99_999_999
    assert response_body["status"] == "pending"
    assert response_body["description"] is None
    assert response_body["processed_at"] is None


def test_create_payment_description_500_characters_success(
    client: TestClient,
    api_key,
):
    _ = api_key

    description = "a" * 500

    response: httpx.Response = client.post(
        "/api/v1/payments",
        headers={"Authorization": "Bearer test_api_key"},
        json={
            "merchant_order_id": "description_500_characters_success",
            "amount_kopecks": 99_999_999,
            "description": description,
        },
    )

    response_body = response.json()

    assert response.status_code == 200
    assert response_body["description"] == description
    assert len(response_body["description"]) == 500


def test_create_payment_description_501_characters_returns_422(
    client: TestClient,
    api_key,
):
    _ = api_key

    description = "a" * 501

    response: httpx.Response = client.post(
        "/api/v1/payments",
        headers={"Authorization": "Bearer test_api_key"},
        json={
            "merchant_order_id": "description_501_characters_returns_422",
            "amount_kopecks": 99_999_999,
            "description": description,
        },
    )

    response_body = response.json()

    assert response.status_code == 422
    assert response_body["detail"][0]["loc"] == ["body", "description"]


def test_create_payment_merchant_order_id_128_characters_success(
    api_key,
    create_payment,
):
    _ = api_key
    merchant_order_id = "a" * 128
    create_response = create_payment(
        merchant_order_id=merchant_order_id,
        amount_kopecks=10000,
        description="merchant_order_id 128 chars success",
    )

    assert create_response.status_code == 200
    assert create_response.json()["merchant_order_id"] == merchant_order_id


def test_create_payment_merchant_order_id_129_characters_returns_422(
    api_key,
    create_payment,
):
    _ = api_key
    merchant_order_id = "a" * 129
    create_response = create_payment(
        merchant_order_id=merchant_order_id,
        amount_kopecks=10000,
        description="merchant_order_id 129 chars returns_422",
    )

    assert create_response.status_code == 422
    assert create_response.json()["detail"][0]["loc"] == ["body", "merchant_order_id"]


def test_create_payment_merchant_order_id_empty_string_returns_422(
    api_key,
    create_payment,
):
    _ = api_key
    merchant_order_id = ""
    create_response = create_payment(
        merchant_order_id=merchant_order_id,
        amount_kopecks=10000,
        description="merchant_order_id empty_string",
    )

    assert create_response.status_code == 422
    assert create_response.json()["detail"][0]["loc"] == ["body", "merchant_order_id"]


def test_create_payment_missing_merchant_order_id_returns_422(
    client: TestClient,
    api_key,
):
    _ = api_key

    response: httpx.Response = client.post(
        "/api/v1/payments",
        headers={"Authorization": "Bearer test_api_key"},
        json={
            "amount_kopecks": 10000,
            "description": "missing merchant_order_id",
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "merchant_order_id"]


@pytest.mark.parametrize("amount_kopecks", [5_000, 100_000_000])
def test_create_payment_amount_boundary_values_success(
    api_key,
    create_payment,
    amount_kopecks: int,
):
    _ = api_key

    response = create_payment(
        merchant_order_id=f"amount_boundary_{amount_kopecks}",
        amount_kopecks=amount_kopecks,
        description="amount boundary value",
    )

    assert response.status_code == 200
    assert response.json()["amount_kopecks"] == amount_kopecks


def test_create_payment_missing_amount_kopecks_returns_422(
    client: TestClient,
    api_key,
):
    _ = api_key

    response: httpx.Response = client.post(
        "/api/v1/payments",
        headers={"Authorization": "Bearer test_api_key"},
        json={
            "merchant_order_id": "missing_amount_kopecks",
            "description": "missing amount_kopecks",
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "amount_kopecks"]


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


def test_create_payment_duplicate_same_data_returns_existing_payment(
    api_key: ApiKey,
    create_payment,
):
    _ = api_key

    response_1 = create_payment(
        merchant_order_id="order_duplicate_same_data",
        amount_kopecks=5000,
        description="test",
    )
    payment_id_1 = response_1.json()["id"]

    response_2 = create_payment(
        merchant_order_id="order_duplicate_same_data",
        amount_kopecks=5000,
        description="test",
    )
    payment_id_2 = response_2.json()["id"]

    assert response_1.status_code == 200
    assert response_2.status_code == 200
    assert payment_id_1 == payment_id_2


def test_create_payment_duplicate_same_merchant_order_id_but_different_amount(
    api_key: ApiKey,
    create_payment,
):
    _ = api_key

    response_1 = create_payment(
        merchant_order_id="order_duplicate_different_amount",
        amount_kopecks=5000,
        description="test",
    )
    response_2 = create_payment(
        merchant_order_id="order_duplicate_different_amount",
        amount_kopecks=45000,
        description="test",
    )

    assert response_1.status_code == 200
    assert response_2.status_code == 409
    assert response_2.json() == {"detail": "Payment already exists with different data"}


# List payments GET /api/v1/payments


def test_list_payments_success(
    client: TestClient,
    api_key: ApiKey,
    create_payment,
):
    _ = api_key

    older_payment_response = create_payment(
        merchant_order_id="list_payments_older",
        amount_kopecks=10_000,
        description="older payment",
    )
    newer_payment_response = create_payment(
        merchant_order_id="list_payments_newer",
        amount_kopecks=20_000,
        description="newer payment",
    )

    response: httpx.Response = client.get(
        "/api/v1/payments",
        headers={"Authorization": "Bearer test_api_key"},
    )
    response_body = response.json()

    assert response.status_code == 200
    assert len(response_body) == 2
    assert response_body[0]["id"] == newer_payment_response.json()["id"]
    assert response_body[1]["id"] == older_payment_response.json()["id"]
    assert response_body[0]["merchant_order_id"] == "list_payments_newer"
    assert response_body[1]["merchant_order_id"] == "list_payments_older"


def test_list_payments_without_authorization_returns_401(client: TestClient):
    response: httpx.Response = client.get("/api/v1/payments")

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_list_payments_returns_only_current_merchant_payments(
    client: TestClient,
    api_key: ApiKey,
    create_api_key,
    create_payment,
):
    _ = api_key
    create_api_key(
        organization_name="Other Merchant",
        api_key_name="Other API key",
        raw_api_key="other_api_key",
    )

    merchant_a_payment_response = create_payment(
        merchant_order_id="merchant_a_list_payment",
        amount_kopecks=10_000,
        description="merchant A payment",
    )
    merchant_b_payment_response = create_payment(
        merchant_order_id="merchant_b_list_payment",
        amount_kopecks=20_000,
        description="merchant B payment",
        raw_api_key="other_api_key",
    )

    response: httpx.Response = client.get(
        "/api/v1/payments",
        headers={"Authorization": "Bearer other_api_key"},
    )
    response_body = response.json()

    returned_payment_ids = [payment["id"] for payment in response_body]

    assert response.status_code == 200
    assert returned_payment_ids == [merchant_b_payment_response.json()["id"]]
    assert merchant_a_payment_response.json()["id"] not in returned_payment_ids


# Get payment by id /api/v1/payments/{payment_id}


def test_get_payment_by_id_success(
    client: TestClient,
    api_key: ApiKey,
    create_payment,
):
    _ = api_key

    create_response = create_payment(
        merchant_order_id="order_get_by_id",
        amount_kopecks=150000,
        description="get by id test",
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


def test_get_payment_by_id_without_authorization(
    client: TestClient,
    api_key: ApiKey,
    create_payment,
):
    _ = api_key

    create_response = create_payment(
        merchant_order_id="123DCX-3241SS",
        amount_kopecks=100_000_000,
        description="test_payment",
    )

    created_response_body = create_response.json()
    payment_id = created_response_body["id"]

    get_response: httpx.Response = client.get(
        f"/api/v1/payments/{payment_id}",
    )

    assert create_response.status_code == 200
    assert get_response.status_code == 401
    assert get_response.json() == {"detail": "Not authenticated"}


def test_merchant_a_does_not_see_payments_merchant_b_by_id(
    client: TestClient,
    api_key: ApiKey,
    create_api_key,
    create_payment,
):
    _ = api_key
    create_api_key(
        organization_name="Organization_B",
        api_key_name="Other API key",
        raw_api_key="other_api_key",
    )
    create_response = create_payment(
        merchant_order_id="order_tenant_isolation",
        amount_kopecks=98_000_000,
        description="tenant isolation test",
    )

    payment_id = create_response.json()["id"]

    get_response = client.get(
        f"/api/v1/payments/{payment_id}",
        headers={"Authorization": "Bearer other_api_key"},
    )

    assert create_response.status_code == 200
    assert get_response.status_code == 404
    assert get_response.json() == {"detail": "Payment not found"}


# Get payment by merchant order id /api/v1/payments/by-order/{merchant_order_id}


def test_get_payment_by_merchant_order_id_success(
    client: TestClient,
    api_key: ApiKey,
    create_payment,
):
    _ = api_key
    merchant_order_id = "12345"

    create_response = create_payment(
        merchant_order_id=merchant_order_id,
        amount_kopecks=1600000,
        description="get by merchant order id",
    )

    response: httpx.Response = client.get(
        f"/api/v1/payments/by-order/{merchant_order_id}",
        headers={"Authorization": "Bearer test_api_key"},
    )

    body = response.json()

    assert create_response.status_code == 200
    assert response.status_code == 200
    assert body["id"] == create_response.json()["id"]
    assert body["merchant_order_id"] == merchant_order_id
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


def test_get_payment_by_order_id_without_authorization(
    client: TestClient,
    api_key: ApiKey,
    create_payment,
):
    _ = api_key
    order_id = "123DCX-3241SS-0001"

    create_response = create_payment(
        merchant_order_id=order_id,
        amount_kopecks=99_000_000,
        description="test_payment",
    )

    get_response: httpx.Response = client.get(
        f"/api/v1/payments/by-order/{order_id}",
    )

    assert create_response.status_code == 200
    assert get_response.status_code == 401
    assert get_response.json() == {"detail": "Not authenticated"}


def test_merchant_a_does_not_see_payments_merchant_b_by_order_id(
    client: TestClient,
    api_key: ApiKey,
    create_api_key,
    create_payment,
):
    _ = api_key
    create_api_key(
        organization_name="Organization_B",
        api_key_name="Other API key",
        raw_api_key="other_api_key",
    )
    create_response = create_payment(
        merchant_order_id="order_tenant_isolation",
        amount_kopecks=98_000_000,
        description="tenant isolation test",
    )

    merchant_order_id = create_response.json()["merchant_order_id"]

    get_response = client.get(
        f"/api/v1/payments/by-order/{merchant_order_id}",
        headers={"Authorization": "Bearer other_api_key"},
    )

    assert create_response.status_code == 200
    assert get_response.status_code == 404
    assert get_response.json() == {"detail": "Payment not found"}