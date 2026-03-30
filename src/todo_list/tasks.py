import logging
import os
from datetime import datetime, timedelta

from src.todo_list.celery_app import celery_app
from src.todo_list.database import SessionLocal
from src.todo_list.components.task_manager import models


LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

logger = logging.getLogger("celery_task")
logger.setLevel(logging.INFO)

if not logger.handlers:
    file_handler = logging.FileHandler(os.path.join(LOG_DIR, "celery.log"))
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


@celery_app.task
def weekly_progress_report():
    db = SessionLocal()
    try:
        logger.info("Weekly report generation started")

        today = datetime.utcnow()
        week_start = today - timedelta(days=7)

        all_tasks = db.query(models.Task).all()

        completed_this_week = db.query(models.Task).filter(
            models.Task.completed == True,
            models.Task.created_at >= week_start
        ).all()

        new_this_week = db.query(models.Task).filter(
            models.Task.created_at >= week_start
        ).all()

        still_incomplete = db.query(models.Task).filter(
            models.Task.completed == False
        ).all()

        user_performance = {}

        for task in all_tasks:
            owner_id = str(task.owner_id)

            if owner_id not in user_performance:
                user_performance[owner_id] = {
                    "total": 0,
                    "completed": 0,
                    "incomplete": 0,
                    "completion_rate": "0%"
                }

            user_performance[owner_id]["total"] += 1

            if task.completed:
                user_performance[owner_id]["completed"] += 1
            else:
                user_performance[owner_id]["incomplete"] += 1

        for user_id, data in user_performance.items():
            if data["total"] > 0:
                rate = (data["completed"] / data["total"]) * 100
                data["completion_rate"] = f"{rate:.1f}%"

        overall_rate = (
            (len(completed_this_week) / len(new_this_week) * 100)
            if new_this_week else 0
        )

        report = {
            "report_date": today.strftime("%Y-%m-%d"),
            "week_start": week_start.strftime("%Y-%m-%d"),
            "week_end": today.strftime("%Y-%m-%d"),
            "summary": {
                "total_tasks": len(all_tasks),
                "new_this_week": len(new_this_week),
                "completed_this_week": len(completed_this_week),
                "still_incomplete": len(still_incomplete),
                "overall_completion_rate": f"{overall_rate:.1f}%"
            },
            "user_performance": user_performance
        }

        logger.info("Weekly report generated successfully")
        logger.info(f"Summary: {report['summary']}")

        for user_id, data in user_performance.items():
            logger.info(f"User {user_id} -> {data}")

        return report

    except Exception as e:
        logger.error(f"Error generating weekly report: {str(e)}")
        raise

    finally:
        db.close()