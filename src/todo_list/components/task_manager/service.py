from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from . import repository, auth
from . import models, schemas
import json
from todo_list.redis_client import redis_client


def register_user_service(db, user):
    hashed = auth.hash_password(user.password)
    user_data = {
        "username": user.username,
        "password": hashed,
        "role": user.role
    }
    try:
        return repository.create_user(db, user_data)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Username already exists")


def send_otp_service(username):
    return auth.generate_otp(username)


def verify_otp_service(db, username, otp):
    if not auth.verify_otp(username, otp):
        return None

    user = repository.get_user(db, username)

    token = auth.create_token({"sub": user.username, "role": user.role})
    return token


def create_task_service(db, task, current_user):
    if current_user["role"] not in ["admin", "manager", "user"]:
        raise Exception("Not allowed to create task")

    new_task = repository.create_task(db, task)

    redis_client.delete("tasks:all")

    return new_task


def get_tasks_service(db, current_user):
    cached = redis_client.get("tasks:all")

    if cached:
        print("✅ Redis se mila!")
        return json.loads(cached)

    print("🔄 DB se le raha hun...")
    tasks = repository.get_tasks(db)

    tasks_data = [
        {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "completed": task.completed,
            "owner_id": task.owner_id
        }
        for task in tasks
    ]

    redis_client.setex(
        "tasks:all",
        300,
        json.dumps(tasks_data)
    )

    return tasks_data

def delete_task_service(db, task_id, current_user):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin can delete")  # ← HTTPException

    result = repository.delete_task(db, task_id)
    redis_client.delete("tasks:all")
    return result
