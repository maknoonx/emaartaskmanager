# tasks/services/notification_service.py
# Create this new file for email notification services

import logging
from datetime import datetime, timedelta
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from ..notification_models import (
    NotificationPreference, 
    EmailNotificationLog, 
    NotificationTemplate
)
from ..models import Task

Employee = get_user_model()
logger = logging.getLogger('notifications')

class EmailNotificationService:
    """
    Service class for handling email notifications
    """
    
    def __init__(self):
        self.from_email = getattr(settings, 'TASK_NOTIFICATION_FROM_EMAIL', settings.DEFAULT_FROM_EMAIL)
        self.enabled = getattr(settings, 'TASK_NOTIFICATION_ENABLED', True)
        self.site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
        self.site_name = getattr(settings, 'SITE_NAME', 'نظام إدارة جمعية إعمار')
    
    def send_task_assigned_notification(self, task, assignee, assigner):
        """
        Send notification when a task is assigned to someone
        """
        if not self.enabled:
            logger.info("Email notifications are disabled")
            return False
        
        # Check user preferences
        preferences = NotificationPreference.get_or_create_for_user(assignee)
        if not preferences.task_assigned_email or not preferences.email_notifications_enabled:
            logger.info(f"Task assigned email disabled for user {assignee.email}")
            return False
        
        # Prepare context
        context = {
            'task': task,
            'assignee': assignee,
            'assigner': assigner,
            'site_name': self.site_name,
            'site_url': self.site_url,
            'task_url': f"{self.site_url}/tasks/{task.pk}/",
            'task_name': task.name,
            'user_name': assignee.name,
            'assigner_name': assigner.name,
            'due_date': task.due_date.strftime('%Y-%m-%d') if task.due_date else 'غير محدد',
            'project_name': task.project.name if task.project else 'غير محدد',
        }
        
        # Get or create template
        template = self._get_or_create_template('task_assigned')
        
        # Render email content
        subject = template.render_subject(context)
        html_content = self._render_email_template('task_assigned.html', context)
        text_content = self._render_email_template('task_assigned.txt', context)
        
        # Send email
        return self._send_email(
            recipient=assignee,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            notification_type='task_assigned',
            task=task,
            sender=assigner
        )
    
    def send_task_completed_notification(self, task, completer):
        """
        Send notification when a task is completed
        """
        if not self.enabled:
            logger.info("Email notifications are disabled")
            return False
        
        # Notify the task creator
        task_creator = task.created_by
        if task_creator == completer:
            # Don't send notification to self
            return False
        
        # Check user preferences
        preferences = NotificationPreference.get_or_create_for_user(task_creator)
        if not preferences.task_completed_email or not preferences.email_notifications_enabled:
            logger.info(f"Task completed email disabled for user {task_creator.email}")
            return False
        
        # Prepare context
        context = {
            'task': task,
            'task_creator': task_creator,
            'completer': completer,
            'site_name': self.site_name,
            'site_url': self.site_url,
            'task_url': f"{self.site_url}/tasks/{task.pk}/",
            'task_name': task.name,
            'user_name': task_creator.name,
            'completer_name': completer.name,
            'completion_date': timezone.now().strftime('%Y-%m-%d %H:%M'),
            'project_name': task.project.name if task.project else 'غير محدد',
        }
        
        # Get or create template
        template = self._get_or_create_template('task_completed')
        
        # Render email content
        subject = template.render_subject(context)
        html_content = self._render_email_template('task_completed.html', context)
        text_content = self._render_email_template('task_completed.txt', context)
        
        # Send email
        return self._send_email(
            recipient=task_creator,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            notification_type='task_completed',
            task=task,
            sender=completer
        )
    
    def send_task_overdue_notification(self, task):
        """
        Send notification when a task is overdue
        """
        if not self.enabled:
            return False
        
        # Send to both creator and assignee
        recipients = []
        if task.created_by:
            recipients.append(task.created_by)
        if task.assigned_to and task.assigned_to != task.created_by:
            recipients.append(task.assigned_to)
        
        results = []
        for recipient in recipients:
            # Check user preferences
            preferences = NotificationPreference.get_or_create_for_user(recipient)
            if not preferences.task_overdue_email or not preferences.email_notifications_enabled:
                continue
            
            # Prepare context
            context = {
                'task': task,
                'recipient': recipient,
                'site_name': self.site_name,
                'site_url': self.site_url,
                'task_url': f"{self.site_url}/tasks/{task.pk}/",
                'task_name': task.name,
                'user_name': recipient.name,
                'due_date': task.due_date.strftime('%Y-%m-%d') if task.due_date else 'غير محدد',
                'days_overdue': (timezone.now().date() - task.due_date).days if task.due_date else 0,
                'project_name': task.project.name if task.project else 'غير محدد',
            }
            
            # Get or create template
            template = self._get_or_create_template('task_overdue')
            
            # Render email content
            subject = template.render_subject(context)
            html_content = self._render_email_template('task_overdue.html', context)
            text_content = self._render_email_template('task_overdue.txt', context)
            
            # Send email
            result = self._send_email(
                recipient=recipient,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                notification_type='task_overdue',
                task=task
            )
            results.append(result)
        
        return all(results)
    
    def send_daily_digest(self, user):
        """
        Send daily digest of tasks to user
        """
        if not self.enabled:
            return False
        
        # Check user preferences
        preferences = NotificationPreference.get_or_create_for_user(user)
        if not preferences.daily_digest_enabled or not preferences.email_notifications_enabled:
            return False
        
        # Get user's tasks
        today = timezone.now().date()
        
        # Tasks assigned to user
        assigned_tasks = Task.objects.filter(
            assigned_to=user,
            status='new'
        ).select_related('project', 'created_by')
        
        # Tasks created by user
        created_tasks = Task.objects.filter(
            created_by=user,
            status='new'
        ).select_related('project', 'assigned_to')
        
        # Overdue tasks
        overdue_tasks = Task.objects.filter(
            models.Q(assigned_to=user) | models.Q(created_by=user),
            status='new',
            due_date__lt=today
        ).select_related('project', 'created_by', 'assigned_to')
        
        # Due today tasks
        due_today_tasks = Task.objects.filter(
            models.Q(assigned_to=user) | models.Q(created_by=user),
            status='new',
            due_date=today
        ).select_related('project', 'created_by', 'assigned_to')
        
        # If no tasks, don't send digest
        if not any([assigned_tasks, created_tasks, overdue_tasks, due_today_tasks]):
            return False
        
        # Prepare context
        context = {
            'user': user,
            'assigned_tasks': assigned_tasks,
            'created_tasks': created_tasks,
            'overdue_tasks': overdue_tasks,
            'due_today_tasks': due_today_tasks,
            'site_name': self.site_name,
            'site_url': self.site_url,
            'user_name': user.name,
            'today': today.strftime('%Y-%m-%d'),
        }
        
        # Get or create template
        template = self._get_or_create_template('daily_digest')
        
        # Render email content
        subject = template.render_subject(context)
        html_content = self._render_email_template('daily_digest.html', context)
        text_content = self._render_email_template('daily_digest.txt', context)
        
        # Send email
        return self._send_email(
            recipient=user,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            notification_type='daily_digest'
        )
    
    def _send_email(self, recipient, subject, html_content, text_content, 
                   notification_type, task=None, sender=None):
        """
        Send email and log the notification
        """
        try:
            # Create email log entry
            log_entry = EmailNotificationLog.objects.create(
                recipient=recipient,
                sender=sender,
                notification_type=notification_type,
                subject=subject,
                content=text_content,
                task=task,
                to_email=recipient.email,
                from_email=self.from_email,
                status='pending'
            )
            
            # Create email message
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=self.from_email,
                to=[recipient.email],
            )
            
            # Attach HTML version
            email.attach_alternative(html_content, "text/html")
            
            # Send email
            email.send()
            
            # Mark as sent
            log_entry.mark_as_sent()
            logger.info(f"Email sent successfully to {recipient.email} for {notification_type}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {recipient.email}: {str(e)}")
            if 'log_entry' in locals():
                log_entry.mark_as_failed(str(e))
            return False
    
    def _render_email_template(self, template_name, context):
        """
        Render email template with context
        """
        try:
            return render_to_string(f'emails/{template_name}', context)
        except Exception as e:
            logger.error(f"Failed to render template {template_name}: {str(e)}")
            # Return a basic template as fallback
            return self._get_fallback_template(context)
    
    def _get_fallback_template(self, context):
        """
        Get fallback template if main template fails
        """
        return f"""
        مرحباً {context.get('user_name', '')},
        
        {context.get('task_name', 'إشعار من نظام إدارة المهام')}
        
        يرجى زيارة النظام للمزيد من التفاصيل: {self.site_url}
        
        مع تحيات فريق {self.site_name}
        """
    
    def _get_or_create_template(self, template_type):
        """
        Get or create notification template
        """
        try:
            return NotificationTemplate.objects.get(
                template_type=template_type,
                is_active=True
            )
        except NotificationTemplate.DoesNotExist:
            return self._create_default_template(template_type)
    
    def _create_default_template(self, template_type):
        """
        Create default notification template
        """
        templates = {
            'task_assigned': {
                'name': 'تكليف مهمة جديدة',
                'subject_template': 'تم تكليفك بمهمة جديدة - {task_name}',
                'html_template': """
                <h2>مرحباً {user_name}</h2>
                <p>تم تكليفك بمهمة جديدة من قبل {assigner_name}</p>
                <h3>تفاصيل المهمة:</h3>
                <ul>
                    <li><strong>اسم المهمة:</strong> {task_name}</li>
                    <li><strong>المشروع:</strong> {project_name}</li>
                    <li><strong>تاريخ الاستحقاق:</strong> {due_date}</li>
                </ul>
                <p><a href="{task_url}">عرض المهمة</a></p>
                """,
                'text_template': """
                مرحباً {user_name}
                
                تم تكليفك بمهمة جديدة من قبل {assigner_name}
                
                تفاصيل المهمة:
                - اسم المهمة: {task_name}
                - المشروع: {project_name}
                - تاريخ الاستحقاق: {due_date}
                
                لعرض المهمة: {task_url}
                
                مع تحيات فريق {site_name}
                """
            },
            'task_completed': {
                'name': 'إنجاز مهمة',
                'subject_template': 'تم إنجاز المهمة - {task_name}',
                'html_template': """
                <h2>مرحباً {user_name}</h2>
                <p>تم إنجاز المهمة التي كلفت بها {completer_name}</p>
                <h3>تفاصيل المهمة:</h3>
                <ul>
                    <li><strong>اسم المهمة:</strong> {task_name}</li>
                    <li><strong>المشروع:</strong> {project_name}</li>
                    <li><strong>تاريخ الإنجاز:</strong> {completion_date}</li>
                </ul>
                <p><a href="{task_url}">عرض المهمة</a></p>
                """,
                'text_template': """
                مرحباً {user_name}
                
                تم إنجاز المهمة التي كلفت بها {completer_name}
                
                تفاصيل المهمة:
                - اسم المهمة: {task_name}
                - المشروع: {project_name}
                - تاريخ الإنجاز: {completion_date}
                
                لعرض المهمة: {task_url}
                
                مع تحيات فريق {site_name}
                """
            },
            'task_overdue': {
                'name': 'مهمة متأخرة',
                'subject_template': 'تنبيه: مهمة متأخرة - {task_name}',
                'html_template': """
                <h2>مرحباً {user_name}</h2>
                <p style="color: red;"><strong>تنبيه: لديك مهمة متأخرة</strong></p>
                <h3>تفاصيل المهمة:</h3>
                <ul>
                    <li><strong>اسم المهمة:</strong> {task_name}</li>
                    <li><strong>المشروع:</strong> {project_name}</li>
                    <li><strong>تاريخ الاستحقاق:</strong> {due_date}</li>
                    <li><strong>عدد الأيام المتأخرة:</strong> {days_overdue}</li>
                </ul>
                <p><a href="{task_url}">عرض المهمة</a></p>
                """,
                'text_template': """
                مرحباً {user_name}
                
                تنبيه: لديك مهمة متأخرة
                
                تفاصيل المهمة:
                - اسم المهمة: {task_name}
                - المشروع: {project_name}
                - تاريخ الاستحقاق: {due_date}
                - عدد الأيام المتأخرة: {days_overdue}
                
                لعرض المهمة: {task_url}
                
                مع تحيات فريق {site_name}
                """
            },
            'daily_digest': {
                'name': 'الملخص اليومي',
                'subject_template': 'ملخص المهام اليومي - {today}',
                'html_template': """
                <h2>مرحباً {user_name}</h2>
                <p>ملخص مهامك لليوم {today}</p>
                
                {% if overdue_tasks %}
                <h3 style="color: red;">المهام المتأخرة ({{ overdue_tasks|length }})</h3>
                <ul>
                {% for task in overdue_tasks %}
                    <li>{task.name} - {task.project.name if task.project else 'بدون مشروع'}</li>
                {% endfor %}
                </ul>
                {% endif %}
                
                {% if due_today_tasks %}
                <h3 style="color: orange;">المهام المستحقة اليوم ({{ due_today_tasks|length }})</h3>
                <ul>
                {% for task in due_today_tasks %}
                    <li>{task.name} - {task.project.name if task.project else 'بدون مشروع'}</li>
                {% endfor %}
                </ul>
                {% endif %}
                
                {% if assigned_tasks %}
                <h3>المهام المكلف بها ({{ assigned_tasks|length }})</h3>
                <ul>
                {% for task in assigned_tasks %}
                    <li>{task.name} - {task.project.name if task.project else 'بدون مشروع'}</li>
                {% endfor %}
                </ul>
                {% endif %}
                
                <p><a href="{site_url}/tasks/my-tasks/">عرض جميع مهامي</a></p>
                """,
                'text_template': """
                مرحباً {user_name}
                
                ملخص مهامك لليوم {today}
                
                المهام المتأخرة: {overdue_count}
                المهام المستحقة اليوم: {due_today_count}
                المهام المكلف بها: {assigned_count}
                
                لعرض جميع مهامك: {site_url}/tasks/my-tasks/
                
                مع تحيات فريق {site_name}
                """
            }
        }
        
        template_data = templates.get(template_type, templates['task_assigned'])
        
        return NotificationTemplate.objects.create(
            name=template_data['name'],
            template_type=template_type,
            subject_template=template_data['subject_template'],
            html_template=template_data['html_template'],
            text_template=template_data['text_template'],
            is_active=True
        )


# Async version using Celery (optional)
class AsyncEmailNotificationService(EmailNotificationService):
    """
    Async version of email notification service using Celery
    """
    
    def send_task_assigned_notification(self, task, assignee, assigner):
        """Send async task assigned notification"""
        from .tasks import send_task_assigned_email_task
        send_task_assigned_email_task.delay(task.id, assignee.id, assigner.id)
        return True
    
    def send_task_completed_notification(self, task, completer):
        """Send async task completed notification"""
        from .tasks import send_task_completed_email_task
        send_task_completed_email_task.delay(task.id, completer.id)
        return True
    
    def send_task_overdue_notification(self, task):
        """Send async task overdue notification"""
        from .tasks import send_task_overdue_email_task
        send_task_overdue_email_task.delay(task.id)
        return True
    
    def send_daily_digest(self, user):
        """Send async daily digest"""
        from .tasks import send_daily_digest_task
        send_daily_digest_task.delay(user.id)
        return True


# Utility functions
def get_notification_service():
    """
    Get the appropriate notification service based on settings
    """
    use_async = getattr(settings, 'USE_CELERY_FOR_EMAILS', False)
    if use_async:
        return AsyncEmailNotificationService()
    return EmailNotificationService()


def send_welcome_email(user):
    """
    Send welcome email to new user
    """
    service = get_notification_service()
    
    context = {
        'user': user,
        'user_name': user.name,
        'site_name': service.site_name,
        'site_url': service.site_url,
        'login_url': f"{service.site_url}/employees/login/",
    }
    
    subject = f"مرحباً بك في {service.site_name}"
    html_content = service._render_email_template('welcome.html', context)
    text_content = service._render_email_template('welcome.txt', context)
    
    return service._send_email(
        recipient=user,
        subject=subject,
        html_content=html_content,
        text_content=text_content,
        notification_type='welcome'
    )