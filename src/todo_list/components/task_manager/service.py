from . import repository, auth
from . import models, schemas


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
    return repository.create_task(db, task)


def get_tasks_service(db, current_user):
    return repository.get_tasks(db)


def delete_task_service(db, task_id, current_user):
    if current_user["role"] != "admin":
        raise Exception("Only admin can delete")
    return repository.delete_task(db, task_id)