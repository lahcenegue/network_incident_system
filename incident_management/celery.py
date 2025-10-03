"""
Celery configuration for Network Incident Management System
"""
import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'incident_management.settings')

# Create Celery app
app = Celery('incident_management')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Configure periodic tasks
app.conf.beat_schedule = {
    'auto-archive-incidents-every-hour': {
        'task': 'incidents.tasks.auto_archive_eligible_incidents',
        'schedule': crontab(minute=0),  # Run every hour at minute 0
        # Alternative schedules for testing:
        # 'schedule': crontab(minute='*/5'),  # Every 5 minutes
        # 'schedule': 60.0,  # Every 60 seconds
    },
}

app.conf.timezone = 'UTC'


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task to test Celery is working"""
    print(f'Request: {self.request!r}')