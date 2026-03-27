from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from todo_list.database import SessionLocal
from todo_list.components.task_manager.constants import SECRET_KEY, ALGORITHM

# 🔥 IMPORTANT: auto_error=False
bearer_scheme = HTTPBearer(auto_error=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
):
    # 🔥 FIX: credentials check
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = credentials.credentials

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        username = payload.get("sub")
        role = payload.get("role")
        user_id = payload.get("id")

        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        return {"sub": username, "role": role, "id": user_id}

    except JWTError:
        raise HTTPException(status_code=401, detail="Token error")


def require_roles(allowed_roles: list):
    def role_checker(user=Depends(get_current_user)):
        if user["role"] not in allowed_roles:
            raise HTTPException(status_code=403, detail="Not allowed")
        return user

    return role_checker