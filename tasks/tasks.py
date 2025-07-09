# tasks/tasks.py
# Create this file for Celery async tasks (optional)

from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import logging

Employee = get_user_model()
logger = logging.getLogger('notifications')

@shared_task(bind=True, max_retries=3)
def send_task_assigned_email_task(self, task_id, assignee_id, assigner_id):
    """
    Async task to send task assignment email
    """
    try:
        from .models import Task
        from .services.notification_service import EmailNotificationService
        
        task = Task.objects.get(id=task_id)
        assignee = Employee.objects.get(id=assignee_id)
        assigner = Employee.objects.get(id=assigner_id)
        
        service = EmailNotificationService()
        result = service.send_task_assigned_notification(
            task=task,
            assignee=assignee,
            assigner=assigner
        )
        
        if result:
            logger.info(f"Task assignment email sent successfully for task {task_id}")
            return {'status': 'success', 'task_id': task_id}
        else:
            raise Exception("Failed to send email")
            
    except Exception as exc:
        logger.error(f"Failed to send task assignment email: {str(exc)}")
        
        # Retry with exponential backoff
        raise self.retry(
            exc=exc,
            countdown=60 * (2 ** self.request.retries),
            max_retries=3
        )

@shared_task(bind=True, max_retries=3)
def send_task_completed_email_task(self, task_id, completer_id):
    """
    Async task to send task completion email
    """
    try:
        from .models import Task
        from .services.notification_service import EmailNotificationService
        
        task = Task.objects.get(id=task_id)
        completer = Employee.objects.get(id=completer_id)
        
        service = EmailNotificationService()
        result = service.send_task_completed_notification(
            task=task,
            completer=completer
        )
        
        if result:
            logger.info(f"Task completion email sent successfully for task {task_id}")
            return {'status': 'success', 'task_id': task_id}
        else:
            raise Exception("Failed to send email")
            
    except Exception as exc:
        logger.error(f"Failed to send task completion email: {str(exc)}")
        
        # Retry with exponential backoff
        raise self.retry(
            exc=exc,
            countdown=60 * (2 ** self.request.retries),
            max_retries=3
        )

@shared_task(bind=True, max_retries=3)
def send_task_overdue_email_task(self, task_id):
    """
    Async task to send task overdue email
    """
    try:
        from .models import Task
        from .services.notification_service import EmailNotificationService
        
        task = Task.objects.get(id=task_id)
        
        service = EmailNotificationService()
        result = service.send_task_overdue_notification(task=task)
        
        if result:
            logger.info(f"Task overdue email sent successfully for task {task_id}")
            return {'status': 'success', 'task_id': task_id}
        else:
            raise Exception("Failed to send email")
            
    except Exception as exc:
        logger.error(f"Failed to send task overdue email: {str(exc)}")
        
        # Retry with exponential backoff
        raise self.retry(
            exc=exc,
            countdown=60 * (2 ** self.request.retries),
            max_retries=3
        )

@shared_task(bind=True, max_retries=3)
def send_daily_digest_task(self, user_id):
    """
    Async task to send daily digest email
    """
    try:
        from .services.notification_service import EmailNotificationService
        
        user = Employee.objects.get(id=user_id)
        
        service = EmailNotificationService()
        result = service.send_daily_digest(user=user)
        
        if result:
            logger.info(f"Daily digest email sent successfully for user {user_id}")
            return {'status': 'success', 'user_id': user_id}
        else:
            logger.info(f"No daily digest sent for user {user_id} (no tasks or disabled)")
            return {'status': 'skipped', 'user_id': user_id}
            
    except Exception as exc:
        logger.error(f"Failed to send daily digest email: {str(exc)}")
        
        # Retry with exponential backoff
        raise self.retry(
            exc=exc,
            countdown=60 * (2 ** self.request.retries),
            max_retries=3
        )

@shared_task
def send_daily_digests_to_all_users():
    """
    Send daily digest emails to all users who have it enabled
    Run this task once per day via cron job or Celery beat
    """
    from .notification_models import NotificationPreference
    
    try:
        # Get all users with daily digest enabled
        preferences = NotificationPreference.objects.filter(
            daily_digest_enabled=True,
            email_notifications_enabled=True
        ).select_related('user')
        
        total_sent = 0
        total_skipped = 0
        
        for preference in preferences:
            try:
                # Check if it's time to send digest based on user's preferred time
                current_time = timezone.now().time()
                user_digest_time = preference.digest_time
                
                # Send if current time is within 1 hour of preferred time
                time_diff = abs(
                    (current_time.hour * 60 + current_time.minute) - 
                    (user_digest_time.hour * 60 + user_digest_time.minute)
                )
                
                if time_diff <= 60:  # Within 1 hour
                    send_daily_digest_task.delay(preference.user.id)
                    total_sent += 1
                else:
                    total_skipped += 1
                    
            except Exception as e:
                logger.error(f"Failed to queue daily digest for user {preference.user.id}: {str(e)}")
        
        logger.info(f"Daily digest: {total_sent} queued, {total_skipped} skipped")
        return {'queued': total_sent, 'skipped': total_skipped}
        
    except Exception as e:
        logger.error(f"Failed to send daily digests: {str(e)}")
        return {'error': str(e)}

@shared_task
def check_overdue_tasks_and_notify():
    """
    Check for overdue tasks and send notifications
    Run this task daily via cron job or Celery beat
    """
    from .models import Task
    from .notification_models import EmailNotificationLog
    
    try:
        # Get overdue tasks that haven't been notified about recently
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        
        overdue_tasks = Task.objects.filter(
            status='new',
            due_date__lt=today
        ).select_related('created_by', 'assigned_to')
        
        notifications_sent = 0
        
        for task in overdue_tasks:
            # Check if we've already sent an overdue notification in the last 24 hours
            recent_notification = EmailNotificationLog.objects.filter(
                task=task,
                notification_type='task_overdue',
                created_at__gte=yesterday,
                status='sent'
            ).exists()
            
            if not recent_notification:
                send_task_overdue_email_task.delay(task.id)
                notifications_sent += 1
        
        logger.info(f"Overdue tasks check: {notifications_sent} notifications queued")
        return {'notifications_queued': notifications_sent}
        
    except Exception as e:
        logger.error(f"Failed to check overdue tasks: {str(e)}")
        return {'error': str(e)}

@shared_task
def cleanup_old_notification_logs():
    """
    Clean up old notification logs
    Run this task weekly
    """
    try:
        from .signals import cleanup_old_notification_logs
        deleted_count = cleanup_old_notification_logs()
        
        logger.info(f"Cleaned up {deleted_count} old notification logs")
        return {'deleted_count': deleted_count}
        
    except Exception as e:
        logger.error(f"Failed to cleanup notification logs: {str(e)}")
        return {'error': str(e)}

@shared_task
def send_weekly_summary_reports():
    """
    Send weekly summary reports to managers
    Run this task weekly on Sunday
    """
    from .models import Task, Project
    from django.db.models import Count, Q
    
    try:
        # Get managers (users who created projects or have multiple assigned tasks)
        managers = Employee.objects.filter(
            Q(created_projects__isnull=False) |
            Q(created_tasks__isnull=False)
        ).distinct()
        
        reports_sent = 0
        
        for manager in managers:
            # Calculate weekly stats
            week_ago = timezone.now() - timedelta(days=7)
            
            weekly_stats = {
                'tasks_created': Task.objects.filter(
                    created_by=manager,
                    created_at__gte=week_ago
                ).count(),
                'tasks_completed': Task.objects.filter(
                    Q(created_by=manager) | Q(assigned_to=manager),
                    status='finished',
                    updated_at__gte=week_ago
                ).count(),
                'projects_created': Project.objects.filter(
                    created_by=manager,
                    created_at__gte=week_ago
                ).count(),
            }
            
            # Only send if there's activity
            if any(weekly_stats.values()):
                # Here you would create and send the weekly report
                # For now, we'll just log it
                logger.info(f"Weekly report for {manager.email}: {weekly_stats}")
                reports_sent += 1
        
        return {'reports_sent': reports_sent}
        
    except Exception as e:
        logger.error(f"Failed to send weekly reports: {str(e)}")
        return {'error': str(e)}

@shared_task
def update_notification_statistics():
    """
    Update notification delivery statistics
    Run this task daily
    """
    from .notification_models import EmailNotificationLog
    from django.db.models import Count
    
    try:
        today = timezone.now().date()
        
        # Calculate daily stats
        daily_stats = EmailNotificationLog.objects.filter(
            created_at__date=today
        ).values('status').annotate(count=Count('id'))
        
        # Calculate success rate
        total_sent = EmailNotificationLog.objects.filter(
            created_at__date=today
        ).count()
        
        successful_sent = EmailNotificationLog.objects.filter(
            created_at__date=today,
            status='sent'
        ).count()
        
        success_rate = (successful_sent / total_sent * 100) if total_sent > 0 else 0
        
        logger.info(f"Daily notification stats: {dict(daily_stats)}, Success rate: {success_rate:.2f}%")
        
        return {
            'daily_stats': dict(daily_stats),
            'success_rate': success_rate,
            'total_sent': total_sent
        }
        
    except Exception as e:
        logger.error(f"Failed to update notification statistics: {str(e)}")
        return {'error': str(e)}

# Monitoring task
@shared_task
def monitor_email_queue_health():
    """
    Monitor email queue health and alert if issues detected
    """
    from .notification_models import EmailNotificationLog
    
    try:
        # Check for stuck emails (pending for more than 1 hour)
        one_hour_ago = timezone.now() - timedelta(hours=1)
        stuck_emails = EmailNotificationLog.objects.filter(
            status='pending',
            created_at__lt=one_hour_ago
        ).count()
        
        # Check failure rate in last hour
        recent_emails = EmailNotificationLog.objects.filter(
            created_at__gte=one_hour_ago
        )
        
        total_recent = recent_emails.count()
        failed_recent = recent_emails.filter(status='failed').count()
        
        failure_rate = (failed_recent / total_recent * 100) if total_recent > 0 else 0
        
        # Alert if failure rate is high or there are stuck emails
        alerts = []
        if stuck_emails > 0:
            alerts.append(f"{stuck_emails} emails stuck in pending status")
        
        if failure_rate > 20:  # More than 20% failure rate
            alerts.append(f"High failure rate: {failure_rate:.2f}%")
        
        if alerts:
            logger.warning(f"Email queue health issues: {', '.join(alerts)}")
            # You could send an alert email to admins here
        
        return {
            'stuck_emails': stuck_emails,
            'failure_rate': failure_rate,
            'alerts': alerts,
            'health_status': 'unhealthy' if alerts else 'healthy'
        }
        
    except Exception as e:
        logger.error(f"Failed to monitor email queue health: {str(e)}")
        return {'error': str(e), 'health_status': 'unknown'}