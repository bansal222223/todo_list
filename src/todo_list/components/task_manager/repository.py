from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from .models import Task, User
from fastapi import HTTPException
from todo_list.logger import get_task_logger, get_auth_logger, log_error

task_logger = get_task_logger()
auth_logger  = get_auth_logger()


def check_permission(task, owner_id, role):
    if role != "admin" and task.owner_id != owner_id:
        task_logger.warning(f"[TASK] action=PERMISSION_DENIED | task_id={task.id} | user_id={owner_id} | role={role}")
        raise HTTPException(status_code=403, detail="Not allowed")


def create_user(db: Session, user_data):
    try:
        user = User(**user_data)
        db.add(user)
        db.commit()
        db.refresh(user)
        auth_logger.info(f"[USER] action=USER_CREATED | username={user.username} | role={user.role}")
        return user

    except IntegrityError:
        db.rollback()
        auth_logger.warning(f"[USER] action=USER_CREATE_FAILED | reason=username_exists | username={user_data.get('username')}")
        raise HTTPException(status_code=400, detail="Username already exists")

    except Exception as e:
        db.rollback()
        log_error(auth_logger, "create_user", e)
        raise HTTPException(status_code=500, detail="User creation failed")


def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()


def create_task(db: Session, task, owner_id: int):
    try:
        db_task = Task(**task.dict(), owner_id=owner_id)
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
        task_logger.info(f"[TASK] action=DB_CREATED | task_id={db_task.id} | owner_id={owner_id}")
        return db_task

    except Exception as e:
        db.rollback()
        log_error(task_logger, "create_task", e)
        raise HTTPException(status_code=500, detail="Task creation failed")


def delete_task(db: Session, task_id: int, owner_id: int, role: str):
    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        task_logger.warning(f"[TASK] action=DELETE_FAILED | task_id={task_id} | reason=not_found")
        raise HTTPException(status_code=404, detail="Task not found")

    check_permission(task, owner_id, role)

    try:
        db.delete(task)
        db.commit()
        task_logger.info(f"[TASK] action=DB_DELETED | task_id={task_id} | owner_id={owner_id}")
        return {"msg": "Deleted"}

    except Exception as e:
        db.rollback()
        log_error(task_logger, "delete_task", e)
        raise HTTPException(status_code=500, detail="Delete failed")


def get_task_by_id(db: Session, task_id: int):
    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        task_logger.warning(f"[TASK] action=FETCH_FAILED | task_id={task_id} | reason=not_found")
        raise HTTPException(status_code=404, detail="Task not found")

    return task


def get_tasks(db: Session, skip: int = 0, limit: int = 10):
    return db.query(Task).offset(skip).limit(limit).all()


def update_task(db: Session, task_id: int, task_data: dict, owner_id: int, role: str):
    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        task_logger.warning(f"[TASK] action=UPDATE_FAILED | task_id={task_id} | reason=not_found")
        raise HTTPException(status_code=404, detail="Task not found")

    check_permission(task, owner_id, role)

    for key, value in task_data.items():
        setattr(task, key, value)

    try:
        db.commit()
        db.refresh(task)
        task_logger.info(f"[TASK] action=DB_UPDATED | task_id={task_id} | owner_id={owner_id} | fields={list(task_data.keys())}")
        return task

    except Exception as e:
        db.rollback()
        log_error(task_logger, "update_task", e)
        raise HTTPException(status_code=500, detail="Update failed")