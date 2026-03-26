from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from todo_list.components.task_manager import service, schemas
from todo_list.components.task_manager.dependencies import get_db, get_current_user

router = APIRouter()


# 🔐 OTP Request Schema
class OTPRequest(BaseModel):
    username: str


# 🔐 Register
@router.post("/register")
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    return service.register_user_service(db, user)


# 📩 Send OTP (FIXED 🔥)
@router.post("/send-otp")
def send_otp(data: OTPRequest):
    print("🔥 CONTROLLER HIT", flush=True)
    return service.send_otp_service(data.username)


# ✅ Verify OTP
@router.post("/verify-otp")
def verify_otp(data: OTPRequest, otp: str, db: Session = Depends(get_db)):
    print("🔥 VERIFY OTP HIT", flush=True)

    token = service.verify_otp_service(db, data.username, otp)

    if not token:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    return {"access_token": token}


# ➕ Create Task
@router.post("/tasks")
def create_task(
    task: schemas.TaskCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return service.create_task_service(db, task, current_user)


# 📖 Get Tasks
@router.get("/tasks")
def get_tasks(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return service.get_tasks_service(db, current_user)


# ❌ Delete Task
@router.delete("/tasks/{task_id}")
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return service.delete_task_service(db, task_id, current_user)