import pytest
from todo_list.components.task_manager import auth
import unittest.mock as mock


class TestRegister:
    def test_register_success(self, client):
        res = client.post("/register", json={
            "username": "testuser", "password": "Test@1234"
        })
        assert res.status_code == 200

    def test_register_duplicate_username(self, client):
        payload = {"username": "testuser", "password": "Test@1234"}
        client.post("/register", json=payload)
        res = client.post("/register", json=payload)
        assert res.status_code == 400

    def test_register_missing_fields(self, client):
        res = client.post("/register", json={})
        assert res.status_code == 422


class TestOTP:
    def test_send_otp_success(self, client):
        client.post("/register", json={
            "username": "testuser", "password": "Test@1234"
        })
        # ✅ Body mein bhejo
        res = client.post("/send-otp", json={"username": "testuser"})
        assert res.status_code == 200

    def test_verify_otp_invalid(self, client):
        client.post("/register", json={
            "username": "testuser", "password": "Test@1234"
        })
        # ✅ Dono body mein — galat OTP
        res = client.post("/verify-otp", json={"username": "testuser", "otp": "000000"})
        assert res.status_code in [400, 404]


class TestProtectedRoute:
    def test_tasks_without_token(self, client):
        res = client.get("/tasks")
        assert res.status_code == 401


class TestAuthFunctions:
    def test_verify_password_success(self):
        hashed = auth.hash_password("Test@1234")
        assert auth.verify_password("Test@1234", hashed) == True

    def test_verify_password_wrong(self):
        hashed = auth.hash_password("Test@1234")
        assert auth.verify_password("WrongPass", hashed) == False

    def test_verify_otp_not_found(self):
        result = auth.verify_otp("nonexistent_user", "123456")
        assert result == False

    def test_verify_otp_wrong_otp(self):
        auth.generate_otp("testuser2")
        result = auth.verify_otp("testuser2", "000000")
        assert result == False

    def test_verify_otp_expired(self):
        # ✅ Redis None return karo — expired simulate karo
        with mock.patch(
            "todo_list.components.task_manager.auth.redis_client"
        ) as mock_r:
            mock_r.get.return_value = None
            result = auth.verify_otp("expireduser", "123456")
            assert result == False