from jose import jwt
from datetime import datetime, timedelta
from todo_list.components.task_manager.constants import SECRET_KEY, ALGORITHM 
import bcrypt
import random



otp_store = {}


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))

def create_token(user):    
    print("USER DATA:", user)                         
    payload = {
        "sub": user["sub"],
        "role": user["role"],
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def generate_otp(username: str):
    otp = str(random.randint(100000, 999999))
    expiry = datetime.utcnow() + timedelta(minutes=5)
    otp_store[username] = {"otp": otp, "expiry": expiry}
    print(f"OTP for {username}: {otp}")
    return {"msg": "OTP sent"}

def verify_otp(username: str, otp: str):
    data = otp_store.get(username)
    if not data:
        return False
    if data["otp"] != otp:
        return False
    if datetime.utcnow() > data["expiry"]:
        return False
    del otp_store[username]
    return True