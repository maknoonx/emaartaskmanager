# eemar_association/celery.py
# تحديث إعدادات Celery لإضافة تذكيرات مواعيد انتهاء المهام

import os
from celery import Celery
from celery.schedules import crontab
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
    # إرسال تذكيرات المهام قريبة الانتهاء (يومياً في الساعة 9 صباحاً)
    'send-task-deadline-reminders': {
        'task': 'tasks.deadline_notifications.send_task_deadline_reminders',
        'schedule': crontab(hour=9, minute=0),  # 9:00 AM daily
        'options': {'queue': 'periodic'}
    },
    
    # فحص إضافي للمهام المستحقة اليوم (كل 3 ساعات خلال ساعات العمل)
    'urgent-deadline-check': {
        'task': 'tasks.deadline_notifications.send_task_deadline_reminders',
        'schedule': crontab(minute=0, hour='9,12,15,18'),  # 9 AM, 12 PM, 3 PM, 6 PM
        'options': {'queue': 'periodic'}
    },
    
    # إرسال الملخص اليومي (الموجود مسبقاً)
    'send-daily-digests': {
        'task': 'tasks.tasks.send_daily_digests_to_all_users',
        'schedule': crontab(hour=8, minute=30),  # 8:30 AM daily
        'options': {'queue': 'periodic'}
    },
    
    # فحص المهام المتأخرة (كل ساعتين خلال ساعات العمل)
    'check-overdue-tasks': {
        'task': 'tasks.tasks.check_overdue_tasks_and_notify',
        'schedule': crontab(minute=0, hour='8,10,12,14,16,18'),
        'options': {'queue': 'periodic'}
    },
    
    # تنظيف سجلات الإشعارات القديمة (أسبوعياً يوم الأحد الساعة 2 صباحاً)
    'cleanup-notification-logs': {
        'task': 'tasks.tasks.cleanup_old_notification_logs',
        'schedule': crontab(hour=2, minute=0, day_of_week=0),  # 2 AM every Sunday
        'options': {'queue': 'maintenance'}
    },
    
    # إرسال التقارير الأسبوعية (يوم الأحد الساعة 10 صباحاً)
    'send-weekly-reports': {
        'task': 'tasks.tasks.send_weekly_summary_reports',
        'schedule': crontab(hour=10, minute=0, day_of_week=0),  # 10 AM every Sunday
        'options': {'queue': 'periodic'}
    },
    
    # تحديث إحصائيات الإشعارات (يومياً الساعة 11 مساءً)
    'update-notification-stats': {
        'task': 'tasks.tasks.update_notification_statistics',
        'schedule': crontab(hour=23, minute=0),  # 11 PM daily
        'options': {'queue': 'maintenance'}
    },
    
    # مراقبة صحة قائمة انتظار الإيميلات (كل 15 دقيقة)
    'monitor-email-queue': {
        'task': 'tasks.tasks.monitor_email_queue_health',
        'schedule': crontab(minute='*/15'),  # Every 15 minutes
        'options': {'queue': 'monitoring'}
    },
    
    # تذكير خاص للمهام عالية الأولوية (كل ساعة خلال ساعات العمل)
    'high-priority-task-reminders': {
        'task': 'tasks.deadline_notifications.send_high_priority_reminders',
        'schedule': crontab(minute=30, hour='8,9,10,11,12,13,14,15,16,17'),
        'options': {'queue': 'periodic'}
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
    
    # Task routing - توجيه المهام لطوابير مختلفة
    task_routes={
        # مهام الإيميلات
        'tasks.tasks.send_task_assigned_email_task': {'queue': 'emails'},
        'tasks.tasks.send_task_completed_email_task': {'queue': 'emails'},
        'tasks.tasks.send_task_overdue_email_task': {'queue': 'emails'},
        'tasks.tasks.send_daily_digest_task': {'queue': 'emails'},
        'tasks.deadline_notifications.send_deadline_reminder_email': {'queue': 'emails'},
        
        # المهام الدورية
        'tasks.tasks.send_daily_digests_to_all_users': {'queue': 'periodic'},
        'tasks.tasks.check_overdue_tasks_and_notify': {'queue': 'periodic'},
        'tasks.deadline_notifications.send_task_deadline_reminders': {'queue': 'periodic'},
        'tasks.deadline_notifications.send_high_priority_reminders': {'queue': 'periodic'},
        
        # مهام الصيانة
        'tasks.tasks.cleanup_old_notification_logs': {'queue': 'maintenance'},
        'tasks.tasks.update_notification_statistics': {'queue': 'maintenance'},
        
        # مهام المراقبة
        'tasks.tasks.monitor_email_queue_health': {'queue': 'monitoring'},
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
    
    # Queue configurations
    task_default_queue='default',
    task_queues={
        'default': {
            'exchange': 'default',
            'routing_key': 'default',
        },
        'emails': {
            'exchange': 'emails',
            'routing_key': 'emails',
        },
        'periodic': {
            'exchange': 'periodic',
            'routing_key': 'periodic',
        },
        'maintenance': {
            'exchange': 'maintenance',
            'routing_key': 'maintenance',
        },
        'monitoring': {
            'exchange': 'monitoring',
            'routing_key': 'monitoring',
        },
    },
)

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

# إعداد للبيئة الإنتاجية مع جدولة محسّنة
# يمكن تخصيص هذه الأوقات حسب متطلبات العمل في المؤسسة

"""
ملاحظات حول الجدولة:

1. تذكيرات المواعيد النهائية:
   - الساعة 9 صباحاً: فحص شامل وإرسال جميع التذكيرات
   - كل 3 ساعات: فحص إضافي للمهام المستحقة اليوم

2. المهام المتأخرة:
   - كل ساعتين خلال ساعات العمل (8ص-6م)

3. الملخص اليومي:
   - الساعة 8:30 صباحاً قبل بداية العمل

4. التقارير والصيانة:
   - أسبوعياً يوم الأحد للتقارير والتنظيف

5. المراقبة:
   - كل 15 دقيقة لمراقبة صحة النظام

للتشغيل في بيئة التطوير، يمكن تقليل الفترات الزمنية للاختبار.
"""