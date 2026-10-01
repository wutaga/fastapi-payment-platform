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
def db():
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture()
def api_key(db):
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
