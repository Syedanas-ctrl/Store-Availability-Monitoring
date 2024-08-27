
from celery import Celery
from app.services import *
from datetime import timedelta
from app.config import Config

celery = Celery(
    "worker",
    broker=f"redis://{Config.REDIS_HOST}:{Config.REDIS_PORT}/{Config.REDIS_DB}",
    backend=f"redis://{Config.REDIS_HOST}:{Config.REDIS_PORT}/{Config.REDIS_DB}",
    broker_connection_retry_on_startup=True
)

@celery.task
def poll_store_status():
    store_service.log_store_statuses()

@celery.task(name='tasks.generate_report')
def generate_report(report_id):
    try:
        report_service.generate_report(report_id)
    except Exception as e:
        report_service.mark_report_as_failed(report_id)

# Schedule the task to run every 60 minutes
celery.conf.beat_schedule = {
    'poll-store-status': {
        'task': 'tasks.poll_store_status',
        'schedule': timedelta(minutes=60),
    },
}
