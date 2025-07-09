
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from tasks.services.notification_service import get_notification_service
from tasks.models import Task

Employee = get_user_model()

class Command(BaseCommand):
    help = 'Test email notifications'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            required=True,
            help='Email address to send test notification to',
        )
        parser.add_argument(
            '--type',
            type=str,
            choices=['welcome', 'task_assigned', 'task_completed', 'daily_digest'],
            default='welcome',
            help='Type of notification to test (default: welcome)',
        )
        parser.add_argument(
            '--task-id',
            type=int,
            help='Task ID for task-related notifications',
        )
    
    def handle(self, *args, **options):
        try:
            user = Employee.objects.get(email=options['email'])
        except Employee.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"User with email {options['email']} not found")
            )
            return
        
        notification_service = get_notification_service()
        
        if options['type'] == 'welcome':
            from tasks.services.notification_service import send_welcome_email
            result = send_welcome_email(user)
            
        elif options['type'] == 'daily_digest':
            result = notification_service.send_daily_digest(user)
            
        elif options['type'] in ['task_assigned', 'task_completed']:
            if not options['task_id']:
                self.stdout.write(
                    self.style.ERROR("--task-id is required for task-related notifications")
                )
                return
            
            try:
                task = Task.objects.get(id=options['task_id'])
            except Task.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"Task with ID {options['task_id']} not found")
                )
                return
            
            if options['type'] == 'task_assigned':
                result = notification_service.send_task_assigned_notification(
                    task=task,
                    assignee=user,
                    assigner=task.created_by
                )
            else:  # task_completed
                result = notification_service.send_task_completed_notification(
                    task=task,
                    completer=user
                )
        
        if result:
            self.stdout.write(
                self.style.SUCCESS(f"Test {options['type']} notification sent to {options['email']}")
            )
        else:
            self.stdout.write(
                self.style.ERROR(f"Failed to send test notification to {options['email']}")
            )
