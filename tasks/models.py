from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import datetime



Employee = get_user_model()

class Project(models.Model):
    """
    Project model for managing projects in the association
    """
    
    STATUS_CHOICES = [
        ('new', 'جديد'),
        ('in_progress', 'قيد التنفيذ'),
        ('finished', 'مكتمل'),
    ]
    
    name = models.CharField(
        max_length=200,
        verbose_name="اسم المشروع",
        help_text="اسم المشروع"
    )
    
    description = models.TextField(
        blank=True,
        verbose_name="وصف المشروع",
        help_text="وصف تفصيلي للمشروع"
    )
    
    # Changed from ForeignKey to ManyToManyField for multiple employees
    assigned_employees = models.ManyToManyField(
        Employee,
        blank=True,
        related_name='assigned_projects',
        verbose_name="الموظفين المُعيّنين",
        help_text="الموظفين المسؤولين عن المشروع"
    )
    
    # Keep the original field for backward compatibility (optional)
    primary_assigned_employee = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='primary_assigned_projects',
        verbose_name="الموظف الرئيسي",
        help_text="الموظف الرئيسي المسؤول عن المشروع"
    )
    
    due_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="تاريخ الانتهاء",
        help_text="التاريخ المتوقع لإنجاز المشروع"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
        verbose_name="حالة المشروع",
        help_text="الحالة الحالية للمشروع"
    )
    
    created_by = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='created_projects',
        verbose_name="منشئ المشروع",
        help_text="الموظف الذي أنشأ المشروع"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ الإنشاء"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="تاريخ آخر تحديث"
    )
    
    class Meta:
        verbose_name = "مشروع"
        verbose_name_plural = "المشاريع"
        ordering = ['-created_at']
        
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('tasks:project_detail', kwargs={'pk': self.pk})
    
    def get_status_display_arabic(self):
        """Return Arabic status name"""
        return dict(self.STATUS_CHOICES).get(self.status, self.status)
    
    def get_status_color(self):
        """Return Bootstrap color class for status"""
        colors = {
            'new': 'info',
            'in_progress': 'warning',
            'finished': 'success',
        }
        return colors.get(self.status, 'secondary')
    
    def is_overdue(self):
        """Check if project is overdue"""
        if self.due_date and self.status != 'finished':
            return timezone.now().date() > self.due_date
        return False
    
    def days_remaining(self):
        """Calculate days remaining until due date"""
        if self.due_date and self.status != 'finished':
            diff = self.due_date - timezone.now().date()
            return diff.days
        return None
    
    def progress_percentage(self):
        """Calculate project progress based on status"""
        progress = {
            'new': 10,
            'in_progress': 50,
            'finished': 100,
        }
        return progress.get(self.status, 0)
    
    def can_be_deleted(self):
        """
        Check if project can be deleted
        """
        # Check if project has any tasks
        if hasattr(self, 'tasks') and self.tasks.exists():
            return False
        return True
    
    def get_deletion_blockers(self):
        """
        Return list of reasons why project cannot be deleted
        """
        blockers = []
        if hasattr(self, 'tasks') and self.tasks.exists():
            blockers.append(f"المهام المرتبطة ({self.tasks.count()})")
        return blockers
    
    @property
    def assigned_employees_display(self):
        """Get formatted string of assigned employees"""
        employees = self.assigned_employees.all()
        if not employees.exists():
            return 'غير محدد'
        elif employees.count() == 1:
            return employees.first().name
        else:
            return f"{employees.first().name} و {employees.count() - 1} آخرين"
    
    @property
    def assigned_employees_names(self):
        """Get list of assigned employee names"""
        return [emp.name for emp in self.assigned_employees.all()]
    
    @property
    def assigned_employees_count(self):
        """Get count of assigned employees"""
        return self.assigned_employees.count()
    
    @property
    def primary_assigned_employee_name(self):
        """Get primary assigned employee name or first assigned employee"""
        if self.primary_assigned_employee:
            return self.primary_assigned_employee.name
        elif self.assigned_employees.exists():
            return self.assigned_employees.first().name
        return 'غير محدد'
    
    @property
    def created_by_name(self):
        """Get creator name"""
        return self.created_by.name if self.created_by else 'غير محدد'
    
    # Backward compatibility methods
    @property
    def assigned_employee(self):
        """For backward compatibility - returns primary or first assigned employee"""
        if self.primary_assigned_employee:
            return self.primary_assigned_employee
        elif self.assigned_employees.exists():
            return self.assigned_employees.first()
        return None
    
    @property
    def assigned_employee_name(self):
        """For backward compatibility"""
        return self.primary_assigned_employee_name


class Task(models.Model):
    """
    Task model for managing individual tasks
    """
    
    STATUS_CHOICES = [
        ('new', 'جديد'),
        ('finished', 'مكتمل'),
    ]
    
    name = models.CharField(
        max_length=200,
        verbose_name="اسم المهمة",
        help_text="اسم المهمة"
    )
    
    detail = models.TextField(
        blank=True,
        verbose_name="تفاصيل المهمة",
        help_text="وصف تفصيلي للمهمة"
    )
    
    due_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="تاريخ الانتهاء",
        help_text="التاريخ المتوقع لإنجاز المهمة"
    )
    
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='tasks',
        verbose_name="المشروع",
        help_text="المشروع المرتبط بالمهمة"
    )
    
    assigned_to = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='assigned_tasks',
        verbose_name="مُعيّن إلى",
        help_text="الموظف المُعيّن للمهمة"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
        verbose_name="حالة المهمة",
        help_text="الحالة الحالية للمهمة"
    )
    
    created_by = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='created_tasks',
        verbose_name="منشئ المهمة",
        help_text="الموظف الذي أنشأ المهمة"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ الإنشاء"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="تاريخ آخر تحديث"
    )
    
    class Meta:
        verbose_name = "مهمة"
        verbose_name_plural = "المهام"
        ordering = ['-created_at']
        
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('tasks:task_detail', kwargs={'pk': self.pk})
    
    def get_status_display_arabic(self):
        """Return Arabic status name"""
        return dict(self.STATUS_CHOICES).get(self.status, self.status)
    
    def get_status_color(self):
        """Return Bootstrap color class for status"""
        colors = {
            'new': 'info',
            'finished': 'success',
        }
        return colors.get(self.status, 'secondary')
    
    def is_overdue(self):
        """Check if task is overdue"""
        if self.due_date and self.status != 'finished':
            return timezone.now().date() > self.due_date
        return False
    
    def days_remaining(self):
        """Calculate days remaining until due date"""
        if self.due_date and self.status != 'finished':
            diff = self.due_date - timezone.now().date()
            return diff.days
        return None
    
    def can_be_edited_by(self, user):
        """Check if user can edit this task"""
        # Creator can always edit their own tasks
        if self.created_by == user:
            return True
        # Assigned user can only change status
        return False
    
    def can_be_deleted_by(self, user):
        """Check if user can delete this task"""
        # Only creator can delete the task
        return self.created_by == user
    
    def can_change_status_by(self, user):
        """Check if user can change task status"""
        # Creator and assigned user can change status
        return self.created_by == user or self.assigned_to == user
    
    @property
    def is_assigned(self):
        """Check if task is assigned to someone"""
        return self.assigned_to is not None
    
    @property
    def assigned_to_name(self):
        """Get assigned user name"""
        return self.assigned_to.name if self.assigned_to else 'غير مُعيّن'
    
    @property
    def created_by_name(self):
        """Get creator name"""
        return self.created_by.name if self.created_by else 'غير محدد'
    
    @property
    def project_name(self):
        """Get project name"""
        return self.project.name if self.project else 'غير محدد'
    









class MonthlyGoal(models.Model):
    """
    Monthly goals for employees
    """
    
    MONTH_CHOICES = [
        (1, 'يناير'),
        (2, 'فبراير'), 
        (3, 'مارس'),
        (4, 'أبريل'),
        (5, 'مايو'),
        (6, 'يونيو'),
        (7, 'يوليو'),
        (8, 'أغسطس'),
        (9, 'سبتمبر'),
        (10, 'أكتوبر'),
        (11, 'نوفمبر'),
        (12, 'ديسمبر'),
    ]
    
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='monthly_goals',
        verbose_name="الموظف"
    )
    
    month = models.IntegerField(
        choices=MONTH_CHOICES,
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        verbose_name="الشهر"
    )
    
    year = models.IntegerField(
        default=datetime.now().year,
        validators=[MinValueValidator(2020), MaxValueValidator(2050)],
        verbose_name="السنة"
    )
    
    goals = models.TextField(
        verbose_name="الأهداف",
        help_text="أهداف الموظف لهذا الشهر"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "هدف شهري"
        verbose_name_plural = "الأهداف الشهرية"
        unique_together = ('employee', 'month', 'year')
        ordering = ['-year', '-month']
    
    def __str__(self):
        month_name = dict(self.MONTH_CHOICES)[self.month]
        return f"{self.employee.name} - {month_name} {self.year}"
    
    def get_absolute_url(self):
        return reverse('tasks:monthly_goal_detail', kwargs={'pk': self.pk})
    
    @property
    def month_name(self):
        """Get Arabic month name"""
        return dict(self.MONTH_CHOICES)[self.month]
    
    @property
    def month_year_display(self):
        """Display month and year in Arabic"""
        return f"{self.month_name} {self.year}"
    
    @property
    def goals_count(self):
        """Count number of goals (lines)"""
        return len([goal.strip() for goal in self.goals.split('\n') if goal.strip()])
    
    def can_be_deleted_by(self, user):
        """Check if user can delete this monthly goal"""
        return self.employee == user or user.is_superuser
    
    def can_be_edited_by(self, user):
        """Check if user can edit this monthly goal"""
        return self.employee == user or user.is_superuser