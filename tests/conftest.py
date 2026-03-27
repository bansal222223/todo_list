import os
import pytest
import unittest.mock as mock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

from src.todo_list.main import app
from todo_list.database import Base
from todo_list.components.task_manager.dependencies import get_db

load_dotenv()

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture(autouse=True)
def mock_redis():
    otp_store = {}

    def mock_setex(key, ttl, value):
        otp_store[key] = value
        return True

    def mock_get(key):
        return otp_store.get(key)

    def mock_delete(key):
        otp_store.pop(key, None)
        return True

    with mock.patch("todo_list.components.task_manager.service.redis_client") as mock_service_redis, \
         mock.patch("todo_list.components.task_manager.auth.redis_client") as mock_auth_redis:

        mock_service_redis.get.return_value = None
        mock_service_redis.setex.return_value = True
        mock_service_redis.delete.return_value = True

        mock_auth_redis.setex.side_effect = mock_setex
        mock_auth_redis.get.side_effect = mock_get
        mock_auth_redis.delete.side_effect = mock_delete

        yield mock_service_redis


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(setup_db):
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def auth_client(client):
    client.post("/register", json={
        "username": "testuser",
        "password": "Test@1234"
    })
    client.post("/send-otp", json={"username": "testuser"})

    # ✅ verify_otp directly mock karo
    with mock.patch(
        "todo_list.components.task_manager.auth.verify_otp",
        return_value=True
    ):
        res = client.post("/verify-otp", json={
            "username": "testuser", "otp": "123456"
        })

    print(f"DEBUG VERIFY RES: {res.json()}")
    token = res.json().get("access_token")
    print(f"DEBUG TOKEN: {token}")
    assert token is not None, f"Token None! Response: {res.json()}"
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client