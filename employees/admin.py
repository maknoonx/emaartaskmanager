from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

Employee = get_user_model()

@admin.register(Employee)
class EmployeeAdmin(UserAdmin):
    """
    Custom admin interface for Employee model
    """
    
    # List display configuration
    list_display = (
        'name', 
        'username', 
        'job_number', 
        'job_title', 
        'section_display',
        'email', 
        'mobile_number', 
        'is_active_employee',
        'is_staff',
        'date_joined'
    )
    
    list_display_links = ('name', 'username')
    
    # Filtering options
    list_filter = (
        'section',
        'is_active_employee',
        'is_staff',
        'is_superuser',
        'date_joined',
    )
    
    # Search functionality
    search_fields = (
        'name',
        'username', 
        'email', 
        'job_number', 
        'job_title',
        'mobile_number'
    )
    
    # Ordering
    ordering = ('name',)
    
    # Items per page
    list_per_page = 25
    
    # Fieldsets for add/edit forms
    fieldsets = (
        ('معلومات الحساب', {
            'fields': ('username', 'password', 'email')
        }),
        ('المعلومات الشخصية', {
            'fields': ('name', 'mobile_number')
        }),
        ('المعلومات الوظيفية', {
            'fields': ('job_number', 'job_title', 'section', 'notes')
        }),
        ('الصلاحيات والحالة', {
            'fields': (
                'is_active_employee',
                'is_active', 
                'is_staff', 
                'is_superuser',
                'groups',
                'user_permissions'
            ),
            'classes': ('collapse',)
        }),
        ('التواريخ المهمة', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )
    
    # Fieldsets for adding new employee
    add_fieldsets = (
        ('معلومات الحساب الأساسية', {
            'fields': ('username', 'password1', 'password2', 'email')
        }),
        ('المعلومات الشخصية', {
            'fields': ('name', 'mobile_number')
        }),
        ('المعلومات الوظيفية', {
            'fields': ('job_number', 'job_title', 'section')
        }),
        ('الحالة', {
            'fields': ('is_active_employee', 'is_staff')
        }),
    )
    
    # Read-only fields
    readonly_fields = ('date_joined', 'last_login', 'created_at', 'updated_at')
    
    # Filter horizontal for many-to-many fields
    filter_horizontal = ('groups', 'user_permissions')
    
    # Actions
    actions = [
        'activate_employees', 
        'deactivate_employees',
        'make_staff',
        'remove_staff',
        'export_employees'
    ]
    

    def section_display(self, obj):
        """Display section in Arabic"""
        return obj.get_section_display_arabic()
    section_display.short_description = 'القسم'
    
    def activate_employees(self, request, queryset):
        """Activate selected employees"""
        updated = queryset.update(is_active_employee=True)
        self.message_user(
            request,
            f'تم تفعيل {updated} موظف بنجاح.'
        )
    activate_employees.short_description = 'تفعيل الموظفين المحددين'
    
    def deactivate_employees(self, request, queryset):
        """Deactivate selected employees"""
        updated = queryset.update(is_active_employee=False)
        self.message_user(
            request,
            f'تم إلغاء تفعيل {updated} موظف بنجاح.'
        )
    deactivate_employees.short_description = 'إلغاء تفعيل الموظفين المحددين'
    
    def make_staff(self, request, queryset):
        """Give staff permissions to selected employees"""
        updated = queryset.update(is_staff=True)
        self.message_user(
            request,
            f'تم منح صلاحيات الإدارة لـ {updated} موظف بنجاح.'
        )
    make_staff.short_description = 'منح صلاحيات الإدارة'
    
    def remove_staff(self, request, queryset):
        """Remove staff permissions from selected employees"""
        updated = queryset.update(is_staff=False)
        self.message_user(
            request,
            f'تم إزالة صلاحيات الإدارة من {updated} موظف بنجاح.'
        )
    remove_staff.short_description = 'إزالة صلاحيات الإدارة'
    
    def export_employees(self, request, queryset):
        """Export selected employees to CSV"""
        import csv
        from django.http import HttpResponse
        from datetime import datetime
        
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="employees_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        # Add BOM for proper Arabic display in Excel
        response.write('\ufeff')
        
        writer = csv.writer(response)
        
        # Write header
        writer.writerow([
            'الاسم الكامل',
            'اسم المستخدم', 
            'الرقم الوظيفي',
            'المسمى الوظيفي',
            'القسم',
            'البريد الإلكتروني',
            'رقم الجوال',
            'تاريخ التوظيف',
            'الحالة',
            'تاريخ آخر دخول'
        ])
        
        # Write data
        for employee in queryset:
            writer.writerow([
                employee.name,
                employee.username,
                employee.job_number,
                employee.job_title,
                employee.get_section_display_arabic(),
                employee.email,
                employee.mobile_number,
                employee.last_login.strftime('%Y-%m-%d %H:%M') if employee.last_login else 'لم يدخل'
            ])
        
        return response
    export_employees.short_description = 'تصدير الموظفين المحددين إلى CSV'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related()
    
    def has_delete_permission(self, request, obj=None):
        """Check if user can delete employee"""
        if obj and not obj.can_be_deleted():
            return False
        return super().has_delete_permission(request, obj)
    
    def delete_model(self, request, obj):
        """Override delete to check constraints"""
        if not obj.can_be_deleted():
            from django.contrib import messages
            messages.error(
                request, 
                f'لا يمكن حذف الموظف {obj.name} لأنه مرتبط ببيانات أخرى.'
            )
            return
        super().delete_model(request, obj)
    
    def save_model(self, request, obj, form, change):
        """Override save to add custom logic"""
        # Set username from email if not provided
        if not obj.username and obj.email:
            obj.username = obj.email.split('@')[0]
        
        super().save_model(request, obj, form, change)
        
        # Log the action
        if change:
            self.message_user(request, f'تم تحديث بيانات الموظف {obj.name} بنجاح.')
        else:
            self.message_user(request, f'تم إضافة الموظف {obj.name} بنجاح.')

# Unregister the default User admin and register our custom one
try:
    from django.contrib.auth.models import User
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass