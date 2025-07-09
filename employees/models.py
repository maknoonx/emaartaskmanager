# Updated Employee model to properly handle the new multiple employee relationships

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.urls import reverse

class Employee(AbstractUser):
    """
    Extended User model for employees with additional Arabic-specific fields
    Updated to support multiple project assignments
    """
    
    # Additional required fields
    name = models.CharField(
        max_length=100, 
        verbose_name="الاسم الكامل",
        help_text="اسم الموظف الكامل"
    )
    
    job_title = models.CharField(
        max_length=100, 
        verbose_name="المسمى الوظيفي",
        help_text="المسمى الوظيفي للموظف"
    )
    
    job_number = models.CharField(
        max_length=20, 
        unique=True,
        verbose_name="الرقم الوظيفي",
        help_text="الرقم الوظيفي الفريد للموظف"
    )
    
    email = models.EmailField(
        unique=True,
        verbose_name="البريد الإلكتروني",
        help_text="البريد الإلكتروني الرسمي للموظف"
    )
    
    # Mobile number with Arabic format validation
    mobile_regex = RegexValidator(
        regex=r'^\+?966[0-9]{9}$|^05[0-9]{8}$',
        message="يجب أن يكون رقم الجوال بصيغة صحيحة (مثال: 0501234567 أو +966501234567)"
    )
    mobile_number = models.CharField(
        validators=[mobile_regex],
        max_length=15,
        verbose_name="رقم الجوال",
        help_text="رقم الجوال للموظف"
    )
    
    SECTION_CHOICES = [
        ('hr', 'الموارد البشرية'),
        ('finance', 'المالية'),
        ('projects', 'المشاريع'),
        ('programs', 'البرامج'),
        ('it', 'تقنية المعلومات'),
        ('admin', 'الإدارة العامة'),
        ('field', 'العمل الميداني'),
        ('media', 'الإعلام والتسويق'),
        ('legal', 'الشؤون القانونية'),
        ('planning', 'التخطيط والمتابعة'),
    ]
    
    section = models.CharField(
        max_length=20,
        choices=SECTION_CHOICES,
        verbose_name="القسم",
        help_text="القسم الذي يعمل به الموظف"
    )
    

    
    is_active_employee = models.BooleanField(
        default=True,
        verbose_name="موظف نشط",
        help_text="هل الموظف نشط حالياً"
    )

    
    notes = models.TextField(
        blank=True,
        verbose_name="ملاحظات",
        help_text="ملاحظات إضافية عن الموظف"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "موظف"
        verbose_name_plural = "الموظفين"
        ordering = ['name']
        
    def __str__(self):
        return f"{self.name} ({self.job_number})"
    
    def get_absolute_url(self):
        return reverse('employees:detail', kwargs={'pk': self.pk})
    
    def get_section_display_arabic(self):
        """Return Arabic section name"""
        return dict(self.SECTION_CHOICES).get(self.section, self.section)
    
    def get_full_mobile(self):
        """Format mobile number consistently"""
        if self.mobile_number.startswith('05'):
            return f"+966{self.mobile_number[1:]}"
        return self.mobile_number
    
    def can_be_deleted(self):
        """
        Check if employee can be deleted (not connected to other models)
        Updated to check both assigned_projects and primary_assigned_projects
        """
        # Check for assigned projects (many-to-many)
        if hasattr(self, 'assigned_projects') and self.assigned_projects.exists():
            return False
        
        # Check for primary assigned projects
        if hasattr(self, 'primary_assigned_projects') and self.primary_assigned_projects.exists():
            return False
        
        # Check for created projects
        if hasattr(self, 'created_projects') and self.created_projects.exists():
            return False
            
        # Check for legacy assigned projects (if still exists)
        if hasattr(self, 'legacy_assigned_projects') and self.legacy_assigned_projects.exists():
            return False
            
        # Add more checks for other models as they are implemented
        # if hasattr(self, 'assigned_tasks') and self.assigned_tasks.exists():
        #     return False
        # if hasattr(self, 'created_tasks') and self.created_tasks.exists():
        #     return False
        
        return True
    
    def get_deletion_blockers(self):
        """
        Return list of reasons why employee cannot be deleted
        Updated to include multiple project relationship types
        """
        blockers = []
        
        # Check for assigned projects (many-to-many)
        if hasattr(self, 'assigned_projects') and self.assigned_projects.exists():
            blockers.append(f"المشاريع المُعيّن بها ({self.assigned_projects.count()})")
        
        # Check for primary assigned projects
        if hasattr(self, 'primary_assigned_projects') and self.primary_assigned_projects.exists():
            blockers.append(f"المشاريع التي يقودها ({self.primary_assigned_projects.count()})")
        
        # Check for created projects
        if hasattr(self, 'created_projects') and self.created_projects.exists():
            blockers.append(f"المشاريع المُنشأة ({self.created_projects.count()})")
            
        # Check for legacy assigned projects (if still exists)
        if hasattr(self, 'legacy_assigned_projects') and self.legacy_assigned_projects.exists():
            blockers.append(f"المشاريع المُعيّنة (النظام القديم) ({self.legacy_assigned_projects.count()})")
            
        # Add more checks for other models as they are implemented
        # if hasattr(self, 'assigned_tasks') and self.assigned_tasks.exists():
        #     blockers.append(f"المهام المُعيّنة ({self.assigned_tasks.count()})")
        # if hasattr(self, 'created_tasks') and self.created_tasks.exists():
        #     blockers.append(f"المهام المُنشأة ({self.created_tasks.count()})")
        
        return blockers

    @property
    def display_name(self):
        """Display name for templates"""
        return self.name or self.username
    
    @property
    def total_assigned_projects(self):
        """Get total count of projects this employee is assigned to"""
        count = 0
        if hasattr(self, 'assigned_projects'):
            count += self.assigned_projects.count()
        return count
    
    @property
    def total_primary_projects(self):
        """Get total count of projects this employee leads"""
        count = 0
        if hasattr(self, 'primary_assigned_projects'):
            count += self.primary_assigned_projects.count()
        return count
    
    @property
    def total_created_projects(self):
        """Get total count of projects this employee created"""
        count = 0
        if hasattr(self, 'created_projects'):
            count += self.created_projects.count()
        return count
    
    def get_active_projects(self):
        """Get all active projects this employee is involved in"""
        from django.db.models import Q
        
        if not hasattr(self, 'assigned_projects'):
            return []
        
        # Get projects where employee is assigned or is primary
        active_projects = []
        
        # Projects assigned to (many-to-many)
        assigned_projects = self.assigned_projects.filter(
            status__in=['new', 'in_progress']
        ).distinct()
        
        # Projects leading (primary)
        if hasattr(self, 'primary_assigned_projects'):
            primary_projects = self.primary_assigned_projects.filter(
                status__in=['new', 'in_progress']
            ).distinct()
            
            # Combine and remove duplicates
            project_ids = set()
            for project in list(assigned_projects) + list(primary_projects):
                if project.id not in project_ids:
                    active_projects.append(project)
                    project_ids.add(project.id)
        else:
            active_projects = list(assigned_projects)
        
        return active_projects
    
    def get_project_workload(self):
        """Calculate workload based on assigned projects"""
        active_projects = self.get_active_projects()
        
        workload = {
            'total_projects': len(active_projects),
            'leading_projects': self.total_primary_projects,
            'overdue_projects': sum(1 for p in active_projects if p.is_overdue()),
            'due_soon_projects': sum(1 for p in active_projects 
                                   if p.days_remaining() and p.days_remaining() <= 7 and not p.is_overdue()),
        }
        
        return workload
    
    def save(self, *args, **kwargs):
        # Ensure email is used as username if not provided
        if not self.username and self.email:
            self.username = self.email.split('@')[0]
        super().save(*args, **kwargs)