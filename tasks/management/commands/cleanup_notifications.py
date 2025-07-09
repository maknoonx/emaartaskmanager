

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from eemar_association.dashboard import models
from tasks.notification_models import EmailNotificationLog

class Command(BaseCommand):
    help = 'Clean up old email notification logs'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='Delete logs older than this many days (default: 90)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )
        parser.add_argument(
            '--keep-failed',
            action='store_true',
            help='Keep failed notifications for debugging',
        )
    
    def handle(self, *args, **options):
        cutoff_date = timezone.now() - timedelta(days=options['days'])
        
        # Base query for old logs
        old_logs = EmailNotificationLog.objects.filter(created_at__lt=cutoff_date)
        
        # Optionally keep failed notifications
        if options['keep_failed']:
            old_logs = old_logs.exclude(status='failed')
        
        count = old_logs.count()
        
        if options['dry_run']:
            self.stdout.write(
                self.style.SUCCESS(f"Dry run: Would delete {count} notification logs older than {options['days']} days")
            )
            
            # Show breakdown by status
            if count > 0:
                status_breakdown = old_logs.values('status').annotate(
                    count=models.Count('id')
                ).order_by('status')
                
                self.stdout.write("Breakdown by status:")
                for item in status_breakdown:
                    self.stdout.write(f"  {item['status']}: {item['count']}")
        else:
            deleted_count = old_logs.delete()[0]
            self.stdout.write(
                self.style.SUCCESS(f"Deleted {deleted_count} old notification logs")
            )
