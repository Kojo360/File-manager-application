"""
Celery Configuration - Phase 3
Background task processing setup
"""
import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings_phase3')

# Create Celery app
app = Celery('file_manager')

# Configure Celery using Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all installed Django apps
app.autodiscover_tasks()

# Celery Beat Schedule for periodic tasks
app.conf.beat_schedule = {
    'collect-system-metrics': {
        'task': 'ai_features.tasks.collect_system_metrics',
        'schedule': 300.0,  # Every 5 minutes
    },
    'generate-daily-analytics': {
        'task': 'ai_features.tasks.generate_daily_analytics',
        'schedule': 3600.0 * 24,  # Daily at midnight
    },
    'process-ai-queue': {
        'task': 'ai_features.tasks.process_ai_queue',
        'schedule': 60.0,  # Every minute
    },
}

app.conf.timezone = 'UTC'


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')


# Task routing configuration
app.conf.task_routes = {
    'ai_features.tasks.process_document_classification': {'queue': 'ai_processing'},
    'ai_features.tasks.generate_smart_tags': {'queue': 'ai_processing'},
    'ai_features.tasks.extract_information': {'queue': 'ai_processing'},
    'ai_features.tasks.collect_system_metrics': {'queue': 'monitoring'},
    'ai_features.tasks.generate_daily_analytics': {'queue': 'analytics'},
}

# Task priorities
app.conf.task_default_priority = 5
app.conf.worker_prefetch_multiplier = 1
app.conf.task_acks_late = True
app.conf.worker_max_tasks_per_child = 1000
