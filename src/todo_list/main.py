from fastapi import FastAPI
from todo_list.components.task_manager.controller import router as task_router
from todo_list.components.task_manager import models
from .database import Base, engine

# ✅ Sync app mein yeh bilkul sahi hai
# Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(task_router)

@app.get("/")
def root():
    return {"message": "Todo API is running 🚀"}