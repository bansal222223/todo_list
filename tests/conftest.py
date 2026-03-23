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


# ✅ Redis mock — har test mein Redis bypass hoga
@pytest.fixture(autouse=True)
def mock_redis():
    with mock.patch("todo_list.components.task_manager.service.redis_client") as mocked:
        mocked.get.return_value = None   # Cache miss
        mocked.set.return_value = True
        mocked.setex.return_value = True
        mocked.delete.return_value = True
        yield mocked


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
    client.post("/send-otp?username=testuser")
    with mock.patch(
        "todo_list.components.task_manager.auth.verify_otp",
        return_value=True
    ):
        res = client.post("/verify-otp?username=testuser&otp=123456")
    token = res.json().get("access_token")
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client