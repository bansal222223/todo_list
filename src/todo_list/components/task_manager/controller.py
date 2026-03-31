from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from todo_list.components.task_manager import service, schemas
from todo_list.components.task_manager.dependencies import get_db, get_current_user

router = APIRouter()



class OTPRequest(BaseModel):
    username: str


@router.post("/register")
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    return service.register_user_service(db, user)



class SendOTPRequest(BaseModel):
    username: str

class VerifyOTPRequest(BaseModel):
    username: str
    otp: str



@router.post("/send-otp")
def send_otp(data: SendOTPRequest):
    print(" CONTROLLER HIT", flush=True)
    return service.send_otp_service(data.username)


@router.post("/verify-otp")
def verify_otp(data: VerifyOTPRequest, db: Session = Depends(get_db)):
    print(" VERIFY OTP HIT", flush=True)

    token = service.verify_otp_service(db, data.username, data.otp)

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






@router.delete("/tasks/{task_id}")
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return service.delete_task_service(db, task_id, current_user)



@router.get("/tasks/{task_id}")
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return service.get_task_by_id_service(db, task_id, current_user)



@router.get("/tasks")
def get_tasks(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return service.get_tasks_service(db, current_user, skip, limit)



@router.put("/tasks/{task_id}")
def update_task(
    task_id: int,
    task: schemas.TaskUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return service.update_task_service(db, task_id, task, current_user)