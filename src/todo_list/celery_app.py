import os
from celery import Celery
from celery.schedules import crontab
import logging

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    filename=os.path.join(LOG_DIR, "celery.log"),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

celery_app = Celery(
    "todo_app",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
    include=["src.todo_list.tasks"]
)

celery_app.conf.timezone = "Asia/Kolkata"
celery_app.conf.enable_utc = False

celery_app.conf.beat_schedule = {
    "weekly-progress-report": {
        "task": "src.todo_list.tasks.weekly_progress_report",
        "schedule": crontab(minute="*/1"),
    },
}

celery_app.conf.update(
    task_track_started=True,
    task_time_limit=300,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)