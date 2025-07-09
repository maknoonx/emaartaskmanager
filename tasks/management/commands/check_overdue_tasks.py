
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from tasks.models import Task
from tasks.services.notification_service import get_notification_service
from tasks.notification_models import EmailNotificationLog

class Command(BaseCommand):
    help = 'Check for overdue tasks and send notifications'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days-overdue',
            type=int,
            default=0,
            help='Minimum days overdue to send notification (default: 0)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be sent without actually sending emails',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force send notifications even if recently sent',
        )
    
    def handle(self, *args, **options):
        notification_service = get_notification_service()
        
        # Calculate cutoff date
        cutoff_date = timezone.now().date() - timedelta(days=options['days_overdue'])
        
        # Get overdue tasks
        overdue_tasks = Task.objects.filter(
            status='new',
            due_date__lt=cutoff_date
        ).select_related('created_by', 'assigned_to')
        
        self.stdout.write(f"Found {overdue_tasks.count()} overdue tasks")
        
        notifications_sent = 0
        notifications_skipped = 0
        
        for task in overdue_tasks:
            task_name = task.name[:50] + "..." if len(task.name) > 50 else task.name
            days_overdue = (timezone.now().date() - task.due_date).days
            
            # Check if we've already sent notification recently (unless forced)
            if not options['force']:
                yesterday = timezone.now() - timedelta(hours=24)
                recent_notification = EmailNotificationLog.objects.filter(
                    task=task,
                    notification_type='task_overdue',
                    created_at__gte=yesterday,
                    status='sent'
                ).exists()
                
                if recent_notification:
                    notifications_skipped += 1
                    self.stdout.write(f"- Skipped {task_name} (recently notified)")
                    continue
            
            if options['dry_run']:
                self.stdout.write(f"Would notify for: {task_name} ({days_overdue} days overdue)")
                notifications_sent += 1
            else:
                result = notification_service.send_task_overdue_notification(task)
                if result:
                    notifications_sent += 1
                    self.stdout.write(f"✓ Notified for: {task_name} ({days_overdue} days overdue)")
                else:
                    notifications_skipped += 1
                    self.stdout.write(f"✗ Failed to notify for: {task_name}")
        
        if options['dry_run']:
            self.stdout.write(
                self.style.SUCCESS(f"Dry run complete. Would send {notifications_sent} notifications.")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Overdue check complete. Sent: {notifications_sent}, Skipped: {notifications_skipped}"
                )
            )
