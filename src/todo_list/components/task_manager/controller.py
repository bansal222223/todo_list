from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from todo_list.components.task_manager import service, schemas
from todo_list.components.task_manager.dependencies import get_db, get_current_user
from todo_list.logger import get_auth_logger, get_task_logger

auth_logger = get_auth_logger()
task_logger = get_task_logger()

router = APIRouter()


class SendOTPRequest(BaseModel):
    username: str


class VerifyOTPRequest(BaseModel):
    username: str
    otp: str


@router.post("/register", status_code=200)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    auth_logger.info(f"[REQUEST] POST /register | username={user.username}")
    return service.register_user_service(db, user)


@router.post("/send-otp")
def send_otp(data: SendOTPRequest):
    auth_logger.info(f"[REQUEST] POST /send-otp | username={data.username}")
    return service.send_otp_service(data.username)


@router.post("/verify-otp")
def verify_otp(data: VerifyOTPRequest, db: Session = Depends(get_db)):
    auth_logger.info(f"[REQUEST] POST /verify-otp | username={data.username}")
    token = service.verify_otp_service(db, data.username, data.otp)
    return {
        "access_token": token,
        "token_type": "bearer"
    }


@router.post("/tasks", status_code=200)
def create_task(
    task: schemas.TaskCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    task_logger.info(f"[REQUEST] POST /tasks | user={current_user['sub']}")
    return service.create_task_service(db, task, current_user)


@router.delete("/tasks/{task_id}", status_code=status.HTTP_200_OK)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    task_logger.info(f"[REQUEST] DELETE /tasks/{task_id} | user={current_user['sub']} | role={current_user['role']}")
    return service.delete_task_service(db, task_id, current_user)


@router.get("/tasks/{task_id}")
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    task_logger.info(f"[REQUEST] GET /tasks/{task_id} | user={current_user['sub']}")
    return service.get_task_by_id_service(db, task_id, current_user)


@router.get("/tasks")
def get_tasks(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    task_logger.info(f"[REQUEST] GET /tasks | user={current_user['sub']} | skip={skip} | limit={limit}")
    return service.get_tasks_service(db, current_user, skip, limit)


@router.patch("/tasks/{task_id}")
def update_task(
    task_id: int,
    task: schemas.TaskUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    task_logger.info(f"[REQUEST] PATCH /tasks/{task_id} | user={current_user['sub']}")
    return service.update_task_service(db, task_id, task, current_user)