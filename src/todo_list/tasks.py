# src/todo_list/tasks.py

from src.todo_list.celery_app import celery_app
from src.todo_list.database import SessionLocal
from src.todo_list.components.task_manager import models
from datetime import datetime, timedelta

@celery_app.task
def weekly_progress_report():
    db = SessionLocal()
    try:
        # Is hafte ki date range
        today = datetime.utcnow()
        week_start = today - timedelta(days=7)

        # Is hafte ke saare tasks
        all_tasks = db.query(models.Task).all()

        # Is hafte complete hue tasks
        completed_this_week = db.query(models.Task).filter(
            models.Task.completed == True,
            models.Task.created_at >= week_start
        ).all()

        # Is hafte bane naye tasks
        new_this_week = db.query(models.Task).filter(
            models.Task.created_at >= week_start
        ).all()

        # Abhi bhi incomplete tasks
        still_incomplete = db.query(models.Task).filter(
            models.Task.completed == False
        ).all()

        # Har user ki performance
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

        # Completion rate calculate karo
        for user_id, data in user_performance.items():
            if data["total"] > 0:
                rate = (data["completed"] / data["total"]) * 100
                data["completion_rate"] = f"{rate:.1f}%"

        # Report banao
        report = {
            "report_date": today.strftime("%Y-%m-%d"),
            "week_start": week_start.strftime("%Y-%m-%d"),
            "week_end": today.strftime("%Y-%m-%d"),
            "summary": {
                "total_tasks": len(all_tasks),
                "new_this_week": len(new_this_week),
                "completed_this_week": len(completed_this_week),
                "still_incomplete": len(still_incomplete),
                "overall_completion_rate": f"{(len(completed_this_week)/len(new_this_week)*100):.1f}%" if new_this_week else "0%"
            },
            "user_performance": user_performance
        }

        # Print karo
        print("=" * 50)
        print("📊 WEEKLY PROGRESS REPORT")
        print("=" * 50)
        print(f"📅 Week: {report['week_start']} → {report['week_end']}")
        print(f"📋 Total Tasks      : {report['summary']['total_tasks']}")
        print(f"🆕 New This Week    : {report['summary']['new_this_week']}")
        print(f"✅ Completed        : {report['summary']['completed_this_week']}")
        print(f"❌ Still Incomplete : {report['summary']['still_incomplete']}")
        print(f"🎯 Completion Rate  : {report['summary']['overall_completion_rate']}")
        print("-" * 50)
        print("👤 User Performance:")
        for user_id, data in user_performance.items():
            print(f"   User {user_id}:")
            print(f"   ✅ Completed  : {data['completed']}")
            print(f"   ❌ Incomplete : {data['incomplete']}")
            print(f"   🎯 Rate       : {data['completion_rate']}")
        print("=" * 50)

        return report

    finally:
        db.close()