from celery import Celery
from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "dari_wallet",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.email_tasks",
        "app.tasks.blockchain_tasks",
        "app.tasks.price_tasks"
    ]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    result_expires=3600,
    task_track_started=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    "update-token-prices": {
        "task": "app.tasks.price_tasks.update_token_prices",
        "schedule": settings.PRICE_UPDATE_INTERVAL_MINUTES * 60.0,
    },
    "check-pending-transactions": {
        "task": "app.tasks.blockchain_tasks.check_pending_transactions",
        "schedule": 30.0,  # Every 30 seconds
    },
    "cleanup-expired-otps": {
        "task": "app.tasks.email_tasks.cleanup_expired_otps",
        "schedule": 300.0,  # Every 5 minutes
    },
}

if __name__ == "__main__":
    celery_app.start()
