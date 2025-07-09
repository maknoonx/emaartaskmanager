
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from tasks.services.notification_service import get_notification_service
from tasks.notification_models import NotificationPreference

Employee = get_user_model()

class Command(BaseCommand):
    help = 'Send daily digest emails to all users who have it enabled'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='Send digest to specific user ID only',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be sent without actually sending emails',
        )
    
    def handle(self, *args, **options):
        notification_service = get_notification_service()
        
        if options['user_id']:
            # Send to specific user
            try:
                user = Employee.objects.get(id=options['user_id'])
                if options['dry_run']:
                    self.stdout.write(f"Would send daily digest to: {user.email}")
                else:
                    result = notification_service.send_daily_digest(user)
                    if result:
                        self.stdout.write(
                            self.style.SUCCESS(f"Daily digest sent to {user.email}")
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(f"Daily digest skipped for {user.email} (no tasks or disabled)")
                        )
            except Employee.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"User with ID {options['user_id']} not found")
                )
        else:
            # Send to all eligible users
            preferences = NotificationPreference.objects.filter(
                daily_digest_enabled=True,
                email_notifications_enabled=True
            ).select_related('user')
            
            sent_count = 0
            skipped_count = 0
            
            for preference in preferences:
                user = preference.user
                
                if options['dry_run']:
                    self.stdout.write(f"Would send daily digest to: {user.email}")
                    sent_count += 1
                else:
                    result = notification_service.send_daily_digest(user)
                    if result:
                        sent_count += 1
                        self.stdout.write(f"✓ Sent to {user.email}")
                    else:
                        skipped_count += 1
                        self.stdout.write(f"- Skipped {user.email}")
            
            if options['dry_run']:
                self.stdout.write(
                    self.style.SUCCESS(f"Dry run complete. Would send {sent_count} emails.")
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Daily digests complete. Sent: {sent_count}, Skipped: {skipped_count}"
                    )
                )