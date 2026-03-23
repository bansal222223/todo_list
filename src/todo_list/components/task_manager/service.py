from . import repository, auth
from . import models, schemas
import json
from todo_list.redis_client import redis_client  # ← Redis import karo


def register_user_service(db, user):
    hashed = auth.hash_password(user.password)
    user_data = {
        "username": user.username,
        "password": hashed,
        "role": user.role
    }
    return repository.create_user(db, user_data)


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
    
    # ⚠️ Naya task bana — purana cache delete karo
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
        "tasks:all",        # ← Key
        300,                # ← 5 minutes
        json.dumps(tasks_data)  # Python List → String
    )
    
    return tasks_data


def delete_task_service(db, task_id, current_user):
    if current_user["role"] != "admin":
        raise Exception("Only admin can delete")
    
    result = repository.delete_task(db, task_id)
    
    
    redis_client.delete("tasks:all")
    
    return result
