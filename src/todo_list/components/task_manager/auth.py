from jose import jwt
from datetime import datetime, timedelta
from todo_list.components.task_manager.constants import SECRET_KEY, ALGORITHM 
import bcrypt
import random
from todo_list.redis_client import redis_client  


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_token(user):    
    print("USER DATA:", user)                         
    payload = {
        "sub": user["sub"],
        "role": user["role"],
        "id": user["id"],  
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def generate_otp(username: str):
    username = username.lower()
    otp = str(random.randint(100000, 999999))
    
   
    redis_client.setex(f"otp:{username}", 300, otp)
    
    print(f" OTP for {username}: {otp}", flush=True)
    return otp


def verify_otp(username: str, otp: str):
    username = username.lower()
    
    stored_otp = redis_client.get(f"otp:{username}")
    
    if not stored_otp:
        return False
    
    if stored_otp!= otp:  
        return False
    
   
    redis_client.delete(f"otp:{username}")
    return True