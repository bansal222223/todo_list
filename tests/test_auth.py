import pytest
from todo_list.components.task_manager import auth


class TestRegister:
    def test_register_success(self, client):
        res = client.post("/register", json={
            "username": "testuser",
            "password": "Test@1234"
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
        res = client.post("/send-otp?username=testuser")
        assert res.status_code == 200

    def test_verify_otp_invalid(self, client):
        res = client.post("/verify-otp?username=testuser&otp=000000")
        assert res.status_code in [400, 404]


class TestProtectedRoute:
    def test_tasks_without_token(self, client):
        res = client.get("/tasks")
        assert res.status_code == 401


# ✅ Auth unit tests — directly function test karo
class TestAuthFunctions:
    def test_verify_password_success(self):
        hashed = auth.hash_password("Test@1234")
        assert auth.verify_password("Test@1234", hashed) == True

    def test_verify_password_wrong(self):
        hashed = auth.hash_password("Test@1234")
        assert auth.verify_password("WrongPass", hashed) == False

    def test_verify_otp_not_found(self):
        # Username ka OTP store mein nahi hai
        result = auth.verify_otp("nonexistent_user", "123456")
        assert result == False

    def test_verify_otp_wrong_otp(self):
        # OTP generate karo phir galat OTP dalo
        auth.generate_otp("testuser2")
        result = auth.verify_otp("testuser2", "000000")
        assert result == False

    def test_verify_otp_expired(self):
        from datetime import datetime, timedelta
        # Manually expired OTP store karo
        auth.otp_store["expireduser"] = {
            "otp": "123456",
            "expiry": datetime.utcnow() - timedelta(minutes=10)  # Pehle se expired
        }
        result = auth.verify_otp("expireduser", "123456")
        assert result == False