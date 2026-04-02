from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from todo_list.database import SessionLocal
from todo_list.components.task_manager.constants import SECRET_KEY, ALGORITHM
from todo_list.logger import get_auth_logger

auth_logger = get_auth_logger()

bearer_scheme = HTTPBearer(auto_error=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
):
    try:
        if credentials is None:
            auth_logger.warning("[AUTH] action=NO_TOKEN | reason=missing credentials")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )

        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        username = payload.get("sub")
        role     = payload.get("role")
        user_id  = payload.get("id")

        if username is None:
            auth_logger.warning("[AUTH] action=INVALID_TOKEN | reason=missing sub")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

        auth_logger.debug(f"[AUTH] action=TOKEN_VALID | user={username} | role={role}")
        return {"sub": username, "role": role, "id": user_id}

    except JWTError as e:
        auth_logger.warning(f"[AUTH] action=TOKEN_REJECTED | reason=JWTError | error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    except Exception as e:
        auth_logger.warning(f"[AUTH] action=AUTH_FAILED | error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )


def require_roles(allowed_roles: list):
    def role_checker(user=Depends(get_current_user)):
        try:
            if user["role"] not in allowed_roles:
                auth_logger.warning(f"[AUTH] action=ROLE_DENIED | user={user['sub']} | role={user['role']} | required={allowed_roles}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not allowed"
                )
            auth_logger.debug(f"[AUTH] action=ROLE_ALLOWED | user={user['sub']} | role={user['role']}")
            return user

        except HTTPException:
            raise
        except Exception as e:
            auth_logger.warning(f"[AUTH] action=ROLE_CHECK_ERROR | error={str(e)}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access error"
            )

    return role_checker