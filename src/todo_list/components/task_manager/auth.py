from jose import jwt
from datetime import datetime, timedelta, timezone
from todo_list.components.task_manager.constants import SECRET_KEY, ALGORITHM
import bcrypt
from todo_list.redis_client import redis_client


def hash_password(password: str) -> str:
    try:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    except Exception as e:
        raise Exception(f"Password hashing failed: {str(e)}")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def create_token(user: dict):
    try:
        expire = datetime.now(timezone.utc) + timedelta(hours=24)

        payload = {
            "sub": user["sub"],
            "role": user["role"],
            "id": user["id"],
            "exp": int(expire.timestamp())
        }

        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    except Exception as e:
        print("TOKEN ERROR:", str(e))
        raise Exception(f"Token creation failed: {str(e)}")


def generate_otp(username: str):
    try:
        username = username.lower()

        otp = "123456"

        redis_client.setex(f"otp:{username}", 300, otp)

        print(f"OTP for {username}: {otp}", flush=True)
        return otp

    except Exception as e:
        raise Exception(f"OTP generation failed: {str(e)}")


def verify_otp(username: str, otp: str):
    try:
        username = username.lower()
        stored_otp = redis_client.get(f"otp:{username}")

        if not stored_otp:
            return False

        if stored_otp.decode().strip() != otp.strip():
            return False

        redis_client.delete(f"otp:{username}")
        return True

    except Exception:
        return False