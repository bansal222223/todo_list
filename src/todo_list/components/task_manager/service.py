from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from . import repository, auth
import json
from todo_list.redis_client import redis_client


# 🔐 Register user
def register_user_service(db, user):
    hashed = auth.hash_password(user.password)

    user_data = {
        "username": user.username.lower(),
        "password": hashed,
        "role": user.role
    }

    try:
        return repository.create_user(db, user_data)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Username already exists")


# 📩 Send OTP
def send_otp_service(username):
    print("👉 send_otp_service called", flush=True)

    otp = auth.generate_otp(username)

    print("👉 OTP generated:", otp, flush=True)

    return {"msg": "OTP sent"}


# ✅ Verify OTP
def verify_otp_service(db, username, otp):
    username = username.lower()

    if not auth.verify_otp(username, otp):
        return None

    user = repository.get_user(db, username)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    token = auth.create_token({
        "sub": user.username,
        "role": user.role
    })

    return token


# ➕ Create Task
def create_task_service(db, task, current_user):
    if current_user["role"] not in ["admin", "manager", "user"]:
        raise HTTPException(status_code=403, detail="Not allowed")

    new_task = repository.create_task(db, task)

    try:
        redis_client.delete("tasks:all")
    except Exception as e:
        print("Redis error:", e)

    return new_task


# 📖 Get Tasks
def get_tasks_service(db, current_user):
    try:
        cached = redis_client.get("tasks:all")
    except Exception:
        cached = None

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

    try:
        redis_client.setex("tasks:all", 300, json.dumps(tasks_data))
    except Exception as e:
        print("Redis error:", e)

    return tasks_data


# ❌ Delete Task
def delete_task_service(db, task_id, current_user):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin can delete")

    result = repository.delete_task(db, task_id)

    try:
        redis_client.delete("tasks:all")
    except Exception as e:
        print("Redis error:", e)

    return result 