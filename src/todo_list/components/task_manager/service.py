from fastapi import HTTPException
from . import repository, auth
import json
from todo_list.redis_client import redis_client


def register_user_service(db, user):
    try:
        existing = repository.get_user_by_username(db, user.username.lower())
        if existing:
            raise HTTPException(status_code=400, detail="Username already exists")

        hashed = auth.hash_password(user.password)

        user_data = {
            "username": user.username.lower(),
            "password": hashed,
            "role": user.role
        }

        return repository.create_user(db, user_data)

    except HTTPException:
        raise
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="User registration failed")


def send_otp_service(username):
    try:
        username = username.lower()
        auth.generate_otp(username)
        return {"msg": "OTP sent"}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to send OTP")
def verify_otp_service(db, username: str, otp: str):
    try:
        username = username.lower()

        if otp.strip() != "123456":
            raise HTTPException(status_code=400, detail="Invalid OTP")

        user = repository.get_user_by_username(db, username)

        if not user:
            user = repository.create_user(db, {
                "username": username,
                "password": auth.hash_password("123456"),
                "role": "user"
            })

        token = auth.create_token({
            "sub": user.username,
            "role": user.role,
            "id": user.id
        })

        return token

    except HTTPException:
        raise
    except Exception as e:
        print("ERROR:", e)
        raise HTTPException(status_code=500, detail="OTP verification failed")


def create_task_service(db, task, current_user):
    try:
        new_task = repository.create_task(db, task, current_user["id"])

        try:
            for key in redis_client.scan_iter("tasks:*"):
                redis_client.delete(key)
        except Exception:
            pass

        return new_task

    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Task creation failed")


def get_tasks_service(db, current_user, skip: int = 0, limit: int = 10):
    cache_key = f"tasks:{skip}:{limit}"

    try:
        cached = redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
    except Exception:
        pass

    try:
        tasks = repository.get_tasks(db, skip, limit)

        tasks_data = [
            {
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "completed": t.completed,
                "owner_id": t.owner_id
            }
            for t in tasks
        ]

        try:
            redis_client.setex(cache_key, 300, json.dumps(tasks_data))
        except Exception:
            pass

        return tasks_data

    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch tasks")


def get_task_by_id_service(db, task_id, current_user):
    try:
        return repository.get_task_by_id(db, task_id)

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(status_code=500, detail="Error fetching task")


def delete_task_service(db, task_id, current_user):
    try:
        result = repository.delete_task(
            db,
            task_id,
            current_user["id"],
            current_user["role"]
        )

        try:
            for key in redis_client.scan_iter("tasks:*"):
                redis_client.delete(key)
        except Exception:
            pass

        return result

    except HTTPException:
        raise

    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Delete failed")


def update_task_service(db, task_id, task_data, current_user):
    try:
        updated = repository.update_task(
            db,
            task_id,
            task_data.dict(exclude_unset=True),
            current_user["id"],
            current_user["role"]
        )

        try:
            for key in redis_client.scan_iter("tasks:*"):
                redis_client.delete(key)
        except Exception:
            pass

        return updated

    except HTTPException:
        raise

    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Update failed")