from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from . import repository, auth
import json
from todo_list.redis_client import redis_client



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



def send_otp_service(username):
    auth.generate_otp(username)
    return {"msg": "OTP sent"}



def verify_otp_service(db, username, otp):
    username = username.lower()

    if not auth.verify_otp(username, otp):
        return None

    user = repository.get_user(db, username)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    token = auth.create_token({
        "sub": user.username,
        "role": user.role,
        "id": user.id
    })

    return token



def create_task_service(db, task, current_user):
    new_task = repository.create_task(db, task, current_user["id"])

    for key in redis_client.scan_iter("tasks:*"):
        redis_client.delete(key)

    return new_task



def get_tasks_service(db, current_user, skip: int = 0, limit: int = 10):
    cache_key = f"tasks:{skip}:{limit}"
    redis_client.flushall()
    print("redis cleared")

    try:
        cached = redis_client.get(cache_key)
    except Exception:
        cached = None

    if cached:
        print(" Redis cache hit")
        return json.loads(cached)

    print(" DB call")

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
    except Exception as e:
        print("Redis error:", e)

    return tasks_data



def get_task_by_id_service(db, task_id, current_user):
    return repository.get_task_by_id(db, task_id)



def delete_task_service(db, task_id, current_user):
    result = repository.delete_task(
        db,
        task_id,
        current_user["id"],
        current_user["role"]
    )

   
    for key in redis_client.scan_iter("tasks:*"):
        redis_client.delete(key)

    return result



def update_task_service(db, task_id, task_data, current_user):
    updated = repository.update_task(
        db,
        task_id,
        task_data.dict(exclude_unset=True),
        current_user["id"],
        current_user["role"]
    )

    
    for key in redis_client.scan_iter("tasks:*"):
        redis_client.delete(key)

    return updated
