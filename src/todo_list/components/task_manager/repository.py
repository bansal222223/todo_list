from sqlalchemy.orm import Session
from .models import Task, User
from fastapi import HTTPException


def create_user(db: Session, user_data):
    user = User(**user_data)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()


def create_task(db: Session, task, owner_id: int):
    db_task = Task(**task.dict(), owner_id=owner_id)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


def delete_task(db: Session, task_id: int, owner_id: int, role: str):
    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

   
    if role != "admin" and task.owner_id != owner_id:
        raise HTTPException(status_code=403, detail="Not allowed")

    db.delete(task)
    db.commit()
    return {"msg": "Deleted"}
# Task by ID
def get_task_by_id(db: Session, task_id: int):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


def get_tasks(db: Session, skip: int = 0, limit: int = 10):
    print(" REPO SKIP:", skip, "LIMIT:", limit)
    return db.query(Task).offset(skip).limit(limit).all()


def update_task(db: Session, task_id: int, task_data: dict, owner_id: int, role: str):
    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if role != "admin" and task.owner_id != owner_id:
        raise HTTPException(status_code=403, detail="Not allowed")

    for key, value in task_data.items():
        setattr(task, key, value)

    db.commit()
    db.refresh(task)
    return task