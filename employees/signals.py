from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.core.cache import cache
import logging

Employee = get_user_model()
logger = logging.getLogger('employees')

@receiver(post_save, sender=Employee)
def employee_post_save(sender, instance, created, **kwargs):
    """
    Signal handler for when an employee is saved
    """
    if created:
        logger.info(f'New employee created: {instance.name} ({instance.job_number})')
        
        # Clear cache
        cache.delete('employee_stats')
        cache.delete('active_employees_count')
        
        # Send welcome email (implement if needed)
        # send_welcome_email.delay(instance.pk)
        
    else:
        logger.info(f'Employee updated: {instance.name} ({instance.job_number})')
        
        # Clear cache
        cache.delete('employee_stats')
        cache.delete(f'employee_detail_{instance.pk}')

@receiver(pre_delete, sender=Employee)
def employee_pre_delete(sender, instance, **kwargs):
    """
    Signal handler before an employee is deleted
    """
    logger.warning(f'Employee being deleted: {instance.name} ({instance.job_number})')
    
    # Clear cache
    cache.delete('employee_stats')
    cache.delete('active_employees_count')
    cache.delete(f'employee_detail_{instance.pk}')
    
    # Archive employee data (implement if needed)
    # archive_employee_data.delay(instance.pk)