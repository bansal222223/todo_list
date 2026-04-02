from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from .models import Task, User
from fastapi import HTTPException


def check_permission(task, owner_id, role):
    if role != "admin" and task.owner_id != owner_id:
        raise HTTPException(status_code=403, detail="Not allowed")


def create_user(db: Session, user_data):
    try:
        user = User(**user_data)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Username already exists")

    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="User creation failed")


def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()


def create_task(db: Session, task, owner_id: int):
    try:
        db_task = Task(**task.dict(), owner_id=owner_id)
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
        return db_task

    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Task creation failed")


def delete_task(db: Session, task_id: int, owner_id: int, role: str):
    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    check_permission(task, owner_id, role)

    try:
        db.delete(task)
        db.commit()
        return {"msg": "Deleted"}

    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Delete failed")


def get_task_by_id(db: Session, task_id: int):
    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return task


def get_tasks(db: Session, skip: int = 0, limit: int = 10):
    return db.query(Task).offset(skip).limit(limit).all()


def update_task(db: Session, task_id: int, task_data: dict, owner_id: int, role: str):
    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    check_permission(task, owner_id, role)

    for key, value in task_data.items():
        setattr(task, key, value)

    try:
        db.commit()
        db.refresh(task)
        return task

    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Update failed")