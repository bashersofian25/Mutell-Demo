from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "mutell",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.workers.evaluation_worker",
        "app.workers.aggregation_worker",
        "app.workers.report_worker",
        "app.workers.eval_scheduler",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "app.workers.evaluation_worker.evaluate_slot": {"queue": "evaluation"},
        "app.workers.eval_scheduler.schedule_pending_evaluations": {"queue": "evaluation"},
        "app.workers.aggregation_worker.compute_aggregations": {"queue": "aggregation"},
        "app.workers.report_worker.generate_report": {"queue": "report"},
    },
    beat_schedule={
        "compute-aggregations-every-15-minutes": {
            "task": "app.workers.aggregation_worker.compute_aggregations",
            "schedule": 900.0,
        },
        "schedule-pending-evaluations": {
            "task": "app.workers.eval_scheduler.schedule_pending_evaluations",
            "schedule": 15.0,
        },
    },
)
