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


# ✅ Redis mock (GLOBAL — sab jagah apply hoga)
@pytest.fixture(autouse=True)
def mock_redis():
    with mock.patch("todo_list.redis_client.redis_client") as mocked:
        mocked.get.return_value = None
        mocked.set.return_value = True
        mocked.setex.return_value = True
        mocked.delete.return_value = True
        yield mocked


# ✅ DB setup/teardown
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


# ✅ Test client with DB override
@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


# ✅ Authenticated client (USER)
@pytest.fixture
def auth_client(client):
    username = "testuser"

    # register
    client.post("/register", json={
        "username": username,
        "password": "Test@1234"
    })

    # send OTP
    client.post("/send-otp", json={
        "username": username
    })

    # mock OTP verification
    with mock.patch(
        "todo_list.components.task_manager.auth.verify_otp",
        return_value=True
    ):
        res = client.post("/verify-otp", json={
            "username": username,
            "otp": "123456"
        })

    token = res.json().get("access_token")

    # 🔥 important safety
    assert token is not None

    client.headers.update({"Authorization": f"Bearer {token}"})

    return client


# ✅ Admin client (optional but useful)
@pytest.fixture
def admin_client(client):
    username = "adminuser"

    client.post("/register", json={
        "username": username,
        "password": "Admin@1234",
        "role": "admin"
    })

    client.post("/send-otp", json={
        "username": username
    })

    with mock.patch(
        "todo_list.components.task_manager.auth.verify_otp",
        return_value=True
    ):
        res = client.post("/verify-otp", json={
            "username": username,
            "otp": "123456"
        })

    token = res.json().get("access_token")

    assert token is not None

    client.headers.update({"Authorization": f"Bearer {token}"})

    return client