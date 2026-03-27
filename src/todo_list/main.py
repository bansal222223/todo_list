from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from todo_list.components.task_manager.controller import router as task_router
from todo_list.components.task_manager import models
from .database import Base, engine

app = FastAPI()


# ✅ ONLY RUN ON STARTUP
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(task_router)


@app.get("/")
def root():
    return {"message": "Todo API is running 🚀"}