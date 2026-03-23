# src/todo_list/celery_app.py

from celery import Celery
from celery.schedules import crontab
import os

celery_app = Celery(
    "todo_app",
    broker=os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0"),
    include=["src.todo_list.tasks"]
)

celery_app.conf.beat_schedule = {
    # Har Somwar subah 9 baje report generate karo
    "weekly-progress-report": {
        "task": "src.todo_list.tasks.weekly_progress_report",
        "schedule": crontab(
            hour=9,
            minute=0,
            day_of_week=1  # ← 1 = Monday
        ),
    },
}

celery_app.conf.timezone = "Asia/Kolkata"  # ← Indian time