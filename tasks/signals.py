# tasks/signals.py
# Create this new file for handling task signals

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Task
from .services.notification_service import get_notification_service
import logging

Employee = get_user_model()
logger = logging.getLogger('notifications')

# Store original task state for comparison
_task_original_state = {}

@receiver(pre_save, sender=Task)
def store_original_task_state(sender, instance, **kwargs):
    """
    Store original task state before saving
    """
    if instance.pk:
        try:
            original = Task.objects.get(pk=instance.pk)
            _task_original_state[instance.pk] = {
                'assigned_to': original.assigned_to,
                'status': original.status,
                'created_by': original.created_by,
            }
        except Task.DoesNotExist:
            _task_original_state[instance.pk] = None
    else:
        _task_original_state[instance.pk] = None

@receiver(post_save, sender=Task)
def handle_task_notifications(sender, instance, created, **kwargs):
    """
    Handle email notifications when tasks are created or updated
    """
    try:
        notification_service = get_notification_service()
        
        if created:
            # New task created
            handle_new_task_created(instance, notification_service)
        else:
            # Existing task updated
            handle_task_updated(instance, notification_service)
            
    except Exception as e:
        logger.error(f"Error in task notification handling: {str(e)}")
    finally:
        # Clean up stored state
        if instance.pk in _task_original_state:
            del _task_original_state[instance.pk]

def handle_new_task_created(task, notification_service):
    """
    Handle notifications for newly created tasks
    """
    # Send notification if task is assigned to someone other than creator
    if task.assigned_to and task.assigned_to != task.created_by:
        logger.info(f"Sending task assignment notification for task {task.id}")
        notification_service.send_task_assigned_notification(
            task=task,
            assignee=task.assigned_to,
            assigner=task.created_by
        )

def handle_task_updated(task, notification_service):
    """
    Handle notifications for updated tasks
    """
    original_state = _task_original_state.get(task.pk)
    if not original_state:
        return
    
    # Check if task was assigned to someone new
    if (task.assigned_to != original_state['assigned_to'] and 
        task.assigned_to and task.assigned_to != task.created_by):
        
        logger.info(f"Sending task assignment notification for task {task.id} (reassigned)")
        notification_service.send_task_assigned_notification(
            task=task,
            assignee=task.assigned_to,
            assigner=task.created_by
        )
    
    # Check if task status changed to finished
    if (task.status == 'finished' and 
        original_state['status'] != 'finished'):
        
        # Determine who completed the task
        # For now, we'll assume it was the assigned person or creator
        completer = task.assigned_to if task.assigned_to else task.created_by
        
        logger.info(f"Sending task completion notification for task {task.id}")
        notification_service.send_task_completed_notification(
            task=task,
            completer=completer
        )

# Optional: Signal for when employees are created
@receiver(post_save, sender=Employee)
def handle_employee_created(sender, instance, created, **kwargs):
    """
    Send welcome email when new employee is created
    """
    if created:
        try:
            from .services.notification_service import send_welcome_email
            logger.info(f"Sending welcome email to new employee {instance.email}")
            send_welcome_email(instance)
        except Exception as e:
            logger.error(f"Failed to send welcome email to {instance.email}: {str(e)}")

# Signal for creating default notification preferences
@receiver(post_save, sender=Employee)
def create_notification_preferences(sender, instance, created, **kwargs):
    """
    Create default notification preferences for new employees
    """
    if created:
        try:
            from .notification_models import NotificationPreference
            NotificationPreference.get_or_create_for_user(instance)
            logger.info(f"Created notification preferences for {instance.email}")
        except Exception as e:
            logger.error(f"Failed to create notification preferences for {instance.email}: {str(e)}")

# Additional signal for handling task updates via API or admin
def send_task_assignment_notification_manual(task_id, assignee_id, assigner_id):
    """
    Manually trigger task assignment notification
    Can be used in views or API endpoints
    """
    try:
        task = Task.objects.get(id=task_id)
        assignee = Employee.objects.get(id=assignee_id)
        assigner = Employee.objects.get(id=assigner_id)
        
        notification_service = get_notification_service()
        notification_service.send_task_assigned_notification(
            task=task,
            assignee=assignee,
            assigner=assigner
        )
        logger.info(f"Manual task assignment notification sent for task {task_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to send manual task assignment notification: {str(e)}")
        return False

def send_task_completion_notification_manual(task_id, completer_id):
    """
    Manually trigger task completion notification
    """
    try:
        task = Task.objects.get(id=task_id)
        completer = Employee.objects.get(id=completer_id)
        
        notification_service = get_notification_service()
        notification_service.send_task_completed_notification(
            task=task,
            completer=completer
        )
        logger.info(f"Manual task completion notification sent for task {task_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to send manual task completion notification: {str(e)}")
        return False

# Utility function to check if notifications should be sent
def should_send_notification(user, notification_type):
    """
    Check if notification should be sent to user
    """
    try:
        from .notification_models import NotificationPreference
        preferences = NotificationPreference.get_or_create_for_user(user)
        
        if not preferences.email_notifications_enabled:
            return False
        
        notification_settings = {
            'task_assigned': preferences.task_assigned_email,
            'task_completed': preferences.task_completed_email,
            'task_overdue': preferences.task_overdue_email,
            'project_assigned': preferences.project_assigned_email,
        }
        
        return notification_settings.get(notification_type, False)
    
    except Exception as e:
        logger.error(f"Error checking notification preferences: {str(e)}")
        return False

# Rate limiting function
def check_email_rate_limit(user, notification_type):
    """
    Check if user has exceeded email rate limits
    """
    try:
        from django.utils import timezone
        from datetime import timedelta
        from .notification_models import EmailNotificationLog
        
        # Get rate limits from settings
        from django.conf import settings
        rate_limits = getattr(settings, 'EMAIL_RATE_LIMIT', {
            'MAX_EMAILS_PER_HOUR': 50,
            'MAX_EMAILS_PER_DAY': 200,
        })
        
        now = timezone.now()
        one_hour_ago = now - timedelta(hours=1)
        one_day_ago = now - timedelta(days=1)
        
        # Check hourly limit
        hourly_count = EmailNotificationLog.objects.filter(
            recipient=user,
            created_at__gte=one_hour_ago,
            status='sent'
        ).count()
        
        if hourly_count >= rate_limits['MAX_EMAILS_PER_HOUR']:
            logger.warning(f"Hourly email limit exceeded for user {user.email}")
            return False
        
        # Check daily limit
        daily_count = EmailNotificationLog.objects.filter(
            recipient=user,
            created_at__gte=one_day_ago,
            status='sent'
        ).count()
        
        if daily_count >= rate_limits['MAX_EMAILS_PER_DAY']:
            logger.warning(f"Daily email limit exceeded for user {user.email}")
            return False
        
        return True
    
    except Exception as e:
        logger.error(f"Error checking email rate limit: {str(e)}")
        return True  # Allow email if check fails

# Cleanup function for old notification logs
def cleanup_old_notification_logs():
    """
    Clean up old notification logs (run as periodic task)
    """
    try:
        from django.utils import timezone
        from datetime import timedelta
        from .notification_models import EmailNotificationLog
        
        # Delete logs older than 90 days
        cutoff_date = timezone.now() - timedelta(days=90)
        deleted_count = EmailNotificationLog.objects.filter(
            created_at__lt=cutoff_date
        ).delete()
        
        logger.info(f"Cleaned up {deleted_count[0]} old notification logs")
        return deleted_count[0]
    
    except Exception as e:
        logger.error(f"Error cleaning up notification logs: {str(e)}")
        return 0