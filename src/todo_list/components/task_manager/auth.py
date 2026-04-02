from jose import jwt
from datetime import datetime, timedelta, timezone
from todo_list.components.task_manager.constants import SECRET_KEY, ALGORITHM
import bcrypt
from todo_list.redis_client import redis_client
from todo_list.logger import get_auth_logger, log_error

logger = get_auth_logger()


def hash_password(password: str) -> str:
    try:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    except Exception as e:
        log_error(logger, "hash_password", e)
        raise Exception(f"Password hashing failed: {str(e)}")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception as e:
        log_error(logger, "verify_password", e)
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

        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        logger.debug(f"[AUTH] action=TOKEN_CREATED | user={user['sub']} | role={user['role']}")
        return token

    except Exception as e:
        log_error(logger, "create_token", e)
        raise Exception(f"Token creation failed: {str(e)}")


def generate_otp(username: str):
    try:
        username = username.lower()
        otp = "123456"
        redis_client.setex(f"otp:{username}", 300, otp)
        logger.info(f"[AUTH] action=OTP_GENERATED | user={username}")
        return otp

    except Exception as e:
        log_error(logger, "generate_otp", e)
        raise Exception(f"OTP generation failed: {str(e)}")


def verify_otp(username: str, otp: str):
    try:
        username = username.lower()
        stored_otp = redis_client.get(f"otp:{username}")

        if not stored_otp:
            logger.warning(f"[AUTH] action=OTP_NOT_FOUND | user={username}")
            return False

        stored_str = stored_otp.decode().strip() if isinstance(stored_otp, bytes) else stored_otp.strip()
        if stored_str != otp.strip():
            logger.warning(f"[AUTH] action=OTP_MISMATCH | user={username}")
            return False

        redis_client.delete(f"otp:{username}")
        logger.info(f"[AUTH] action=OTP_VERIFIED | user={username}")
        return True

    except Exception as e:
        log_error(logger, "verify_otp", e)
        return False