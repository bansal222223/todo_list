from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from todo_list.database import SessionLocal
from todo_list.components.task_manager.constants import SECRET_KEY, ALGORITHM

bearer_scheme = HTTPBearer()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    token = credentials.credentials
    print(f"TOKEN RECEIVED: {token}")       # ✅ debug
    print(f"SECRET KEY: {SECRET_KEY}")      # ✅ debug
    print(f"ALGORITHM: {ALGORITHM}")        # ✅ debug
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(f"PAYLOAD: {payload}")        # ✅ debug
        username = payload.get("sub")
        role = payload.get("role")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"username": username, "role": role}
    except JWTError as e:
        print(f"JWT ERROR: {e}")            # ✅ debug
        raise HTTPException(status_code=401, detail="Token error")


def require_roles(allowed_roles: list):
    def role_checker(user=Depends(get_current_user)):
        if user["role"] not in allowed_roles:
            raise HTTPException(status_code=403, detail="Not allowed")
        return user
    return role_checker