from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from todo_list.database import SessionLocal
from todo_list.components.task_manager import service, schemas
from todo_list.components.task_manager.dependencies import get_db, get_current_user

router = APIRouter()

@router.post("/register")
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    return service.register_user_service(db, user)

@router.post("/send-otp")
def send_otp(username: str):
    return service.send_otp_service(username)

@router.post("/verify-otp")
def verify_otp(username: str, otp: str, db: Session = Depends(get_db)):  # ✅ db add kiya
    token = service.verify_otp_service(db, username, otp)  # ✅ db pass kiya

    if not token:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    return {"access_token": token}

@router.post("/tasks")
def create_task(
    task: schemas.TaskCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return service.create_task_service(db, task, current_user)

@router.get("/tasks")
def get_tasks(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return service.get_tasks_service(db, current_user)


@router.delete("/tasks/{task_id}")
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return service.delete_task_service(db, task_id, current_user)