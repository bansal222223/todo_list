from fastapi import HTTPException
from . import repository, auth
import json
from todo_list.redis_client import redis_client
from todo_list.logger import get_auth_logger, get_task_logger, log_user_action, log_task_change, log_error

auth_logger = get_auth_logger()
task_logger = get_task_logger()


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

        new_user = repository.create_user(db, user_data)
        log_user_action(auth_logger, "REGISTER", user.username.lower(), "User registered successfully")
        return new_user

    except HTTPException:
        raise
    except Exception as e:
        log_error(auth_logger, "register_user_service", e)
        db.rollback()
        raise HTTPException(status_code=500, detail="User registration failed")


def send_otp_service(username):
    try:
        username = username.lower()
        auth.generate_otp(username)
        log_user_action(auth_logger, "OTP_SENT", username)
        return {"msg": "OTP sent"}
    except Exception as e:
        log_error(auth_logger, "send_otp_service", e)
        raise HTTPException(status_code=500, detail="Failed to send OTP")


def verify_otp_service(db, username: str, otp: str):
    try:
        username = username.lower()

        if otp.strip() != "123456":
            auth_logger.warning(f"[USER] action=OTP_FAILED | user={username} | Invalid OTP entered")
            raise HTTPException(status_code=400, detail="Invalid OTP")

        user = repository.get_user_by_username(db, username)

        if not user:
            user = repository.create_user(db, {
                "username": username,
                "password": auth.hash_password("123456"),
                "role": "user"
            })
            log_user_action(auth_logger, "USER_AUTO_CREATED", username)

        token = auth.create_token({
            "sub": user.username,
            "role": user.role,
            "id": user.id
        })

        log_user_action(auth_logger, "OTP_VERIFIED", username, f"role={user.role}")
        return token

    except HTTPException:
        raise
    except Exception as e:
        log_error(auth_logger, "verify_otp_service", e)
        raise HTTPException(status_code=500, detail="OTP verification failed")


def create_task_service(db, task, current_user):
    try:
        new_task = repository.create_task(db, task, current_user["id"])

        try:
            for key in redis_client.scan_iter("tasks:*"):
                redis_client.delete(key)
        except Exception:
            pass

        log_task_change(task_logger, "CREATED", new_task.id, current_user["id"], f"title={new_task.title}")
        return new_task

    except Exception as e:
        log_error(task_logger, "create_task_service", e)
        db.rollback()
        raise HTTPException(status_code=500, detail="Task creation failed")


def get_tasks_service(db, current_user, skip: int = 0, limit: int = 10):
    cache_key = f"tasks:{skip}:{limit}"

    try:
        cached = redis_client.get(cache_key)
        if cached:
            task_logger.debug(f"[TASK] action=CACHE_HIT | key={cache_key}")
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

        task_logger.info(f"[TASK] action=FETCHED_ALL | count={len(tasks_data)} | skip={skip} | limit={limit}")
        return tasks_data

    except Exception as e:
        log_error(task_logger, "get_tasks_service", e)
        raise HTTPException(status_code=500, detail="Failed to fetch tasks")


def get_task_by_id_service(db, task_id, current_user):
    try:
        task = repository.get_task_by_id(db, task_id)
        task_logger.info(f"[TASK] action=FETCHED | task_id={task_id} | user_id={current_user['id']}")
        return task

    except HTTPException:
        raise
    except Exception as e:
        log_error(task_logger, "get_task_by_id_service", e)
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

        log_task_change(task_logger, "DELETED", task_id, current_user["id"], f"role={current_user['role']}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        log_error(task_logger, "delete_task_service", e)
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

        log_task_change(task_logger, "UPDATED", task_id, current_user["id"], f"fields={list(task_data.dict(exclude_unset=True).keys())}")
        return updated

    except HTTPException:
        raise
    except Exception as e:
        log_error(task_logger, "update_task_service", e)
        db.rollback()
        raise HTTPException(status_code=500, detail="Update failed")