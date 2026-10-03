from collections.abc import Callable, Generator

import httpx
import pytest
from dotenv import dotenv_values
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.dependencies import get_db
from app.main import app
from app.models import ApiKey, Organization
from app.security.api_keys import hash_api_key

config = dotenv_values(".env.test")

TEST_DATABASE_URL = config["DATABASE_URL"]

test_engine = create_engine(TEST_DATABASE_URL)

TestingSessionLocal = sessionmaker(bind=test_engine)


@pytest.fixture()
def db() -> Generator:
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def client(db) -> Generator[TestClient]:
    def override_get_db():
        try:
            yield db
        except Exception:
            db.rollback()
            raise

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture()
def api_key(db) -> ApiKey:
    organization = Organization(name="Test Merchant")
    db.add(organization)
    db.flush()

    api_key = ApiKey(
        organization_id=organization.id,
        name="Test API key",
        secret_hash=hash_api_key("test_api_key"),
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)

    return api_key


@pytest.fixture()
def create_api_key(db) -> Callable[[str, str, str], ApiKey]:
    def _create_api_key(
        organization_name: str,
        api_key_name: str,
        raw_api_key: str,
    ) -> ApiKey:
        organization = Organization(name=organization_name)
        db.add(organization)
        db.flush()
        api_key = ApiKey(
            organization_id=organization.id,
            name=api_key_name,
            secret_hash=hash_api_key(raw_api_key),
        )
        db.add(api_key)
        db.commit()
        return api_key

    return _create_api_key


@pytest.fixture()
def create_payment(client: TestClient):
    def _create_payment(
        merchant_order_id: str,
        amount_kopecks: int,
        description: str | None,
        raw_api_key: str = "test_api_key",
    ) -> httpx.Response:
        response = client.post(
            "/api/v1/payments",
            headers={"Authorization": f"Bearer {raw_api_key}"},
            json={
                "merchant_order_id": merchant_order_id,
                "amount_kopecks": amount_kopecks,
                "description": description,
            },
        )
        return response

    return _create_payment
