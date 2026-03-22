from sqlalchemy.orm import Session
from .models import Task, User



def create_user(db: Session, user_data):
    user = User(**user_data)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()


#
def create_task(db: Session, task):
    db_task = Task(**task.dict())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task



def get_tasks(db: Session):
    return db.query(Task).all()



def delete_task(db: Session, task_id: int):
    task = db.query(Task).filter(Task.id == task_id).first()

    if task:
        db.delete(task)
        db.commit()

    return {"msg": "Deleted"}