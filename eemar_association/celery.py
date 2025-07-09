# eemar_association/celery.py
# Create this file for Celery configuration

import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eemar_association.settings')

app = Celery('eemar_association')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps
app.autodiscover_tasks()

# Celery Beat Schedule for periodic tasks
app.conf.beat_schedule = {
    # Send daily digests at 9 AM every day
    'send-daily-digests': {
        'task': 'tasks.tasks.send_daily_digests_to_all_users',
        'schedule': 30.0,  # Every 30 seconds for testing, change to crontab for production
        # 'schedule': crontab(hour=9, minute=0),  # 9:00 AM daily
    },
    
    # Check for overdue tasks every hour
    'check-overdue-tasks': {
        'task': 'tasks.tasks.check_overdue_tasks_and_notify',
        'schedule': 60.0,  # Every minute for testing
        # 'schedule': crontab(minute=0),  # Every hour
    },
    
    # Clean up old notification logs weekly
    'cleanup-notification-logs': {
        'task': 'tasks.tasks.cleanup_old_notification_logs',
        'schedule': 300.0,  # Every 5 minutes for testing
        # 'schedule': crontab(hour=2, minute=0, day_of_week=1),  # 2 AM every Monday
    },
    
    # Send weekly reports on Sunday
    'send-weekly-reports': {
        'task': 'tasks.tasks.send_weekly_summary_reports',
        'schedule': 600.0,  # Every 10 minutes for testing
        # 'schedule': crontab(hour=10, minute=0, day_of_week=0),  # 10 AM every Sunday
    },
    
    # Update notification statistics daily
    'update-notification-stats': {
        'task': 'tasks.tasks.update_notification_statistics',
        'schedule': 180.0,  # Every 3 minutes for testing
        # 'schedule': crontab(hour=23, minute=0),  # 11 PM daily
    },
    
    # Monitor email queue health every 15 minutes
    'monitor-email-queue': {
        'task': 'tasks.tasks.monitor_email_queue_health',
        'schedule': 120.0,  # Every 2 minutes for testing
        # 'schedule': crontab(minute='*/15'),  # Every 15 minutes
    },
}

# Celery configuration
app.conf.update(
    # Task settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Riyadh',
    enable_utc=True,
    
    # Result backend settings
    result_expires=3600,  # 1 hour
    
    # Task routing
    task_routes={
        'tasks.tasks.send_task_assigned_email_task': {'queue': 'emails'},
        'tasks.tasks.send_task_completed_email_task': {'queue': 'emails'},
        'tasks.tasks.send_task_overdue_email_task': {'queue': 'emails'},
        'tasks.tasks.send_daily_digest_task': {'queue': 'emails'},
        'tasks.tasks.send_daily_digests_to_all_users': {'queue': 'periodic'},
        'tasks.tasks.check_overdue_tasks_and_notify': {'queue': 'periodic'},
        'tasks.tasks.cleanup_old_notification_logs': {'queue': 'maintenance'},
        'tasks.tasks.update_notification_statistics': {'queue': 'maintenance'},
    },
    
    # Worker settings
    worker_prefetch_multiplier=4,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
    
    # Email task specific settings
    task_soft_time_limit=60,  # 1 minute soft limit
    task_time_limit=120,      # 2 minutes hard limit
    
    # Retry settings
    task_default_retry_delay=60,
    task_max_retries=3,
)

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

# Production beat schedule (uncomment for production)
"""
from celery.schedules import crontab

app.conf.beat_schedule = {
    # Send daily digests at 9 AM every day
    'send-daily-digests': {
        'task': 'tasks.tasks.send_daily_digests_to_all_users',
        'schedule': crontab(hour=9, minute=0),
    },
    
    # Check for overdue tasks every 2 hours during work hours
    'check-overdue-tasks': {
        'task': 'tasks.tasks.check_overdue_tasks_and_notify',
        'schedule': crontab(minute=0, hour='8,10,12,14,16'),
    },
    
    # Clean up old notification logs weekly on Sunday at 2 AM
    'cleanup-notification-logs': {
        'task': 'tasks.tasks.cleanup_old_notification_logs',
        'schedule': crontab(hour=2, minute=0, day_of_week=0),
    },
    
    # Send weekly reports on Sunday at 10 AM
    'send-weekly-reports': {
        'task': 'tasks.tasks.send_weekly_summary_reports',
        'schedule': crontab(hour=10, minute=0, day_of_week=0),
    },
    
    # Update notification statistics daily at 11 PM
    'update-notification-stats': {
        'task': 'tasks.tasks.update_notification_statistics',
        'schedule': crontab(hour=23, minute=0),
    },
    
    # Monitor email queue health every 15 minutes
    'monitor-email-queue': {
        'task': 'tasks.tasks.monitor_email_queue_health',
        'schedule': crontab(minute='*/15'),
    },
}
"""