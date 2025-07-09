from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.contrib.auth import get_user_model
from .models import Project

Employee = get_user_model()

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """
    Custom admin interface for Project model with multiple employees support
    """
    
    # List display configuration
    list_display = (
        'name', 
        'status_display',
        'assigned_team_display',
        'primary_employee_display',
        'progress_display',
        'due_date_display',
        'created_by',
        'created_at_display',
        'is_overdue_display'
    )
    
    list_display_links = ('name',)
    
    # Filtering options
    list_filter = (
        'status',
        'created_at',
        'due_date',
        'assigned_employees__section',
        'primary_assigned_employee__section',
        'created_by__section',
    )
    
    # Search functionality
    search_fields = (
        'name',
        'description',
        'assigned_employees__name',
        'assigned_employees__username',
        'primary_assigned_employee__name',
        'primary_assigned_employee__username',
        'created_by__name',
        'created_by__username'
    )
    
    # Ordering
    ordering = ('-created_at',)
    
    # Items per page
    list_per_page = 25
    
    # Fieldsets for add/edit forms
    fieldsets = (
        ('معلومات المشروع الأساسية', {
            'fields': ('name', 'description')
        }),
        ('فريق العمل والجدولة', {
            'fields': ('assigned_employees', 'primary_assigned_employee', 'due_date', 'status'),
            'description': 'يمكنك تعيين عدة موظفين للمشروع واختيار موظف رئيسي منهم'
        }),
        ('معلومات الإنشاء', {
            'fields': ('created_by',),
            'classes': ('collapse',)
        }),
    )
    
    # Read-only fields
    readonly_fields = ('created_at', 'updated_at')
    
    # Many-to-many fields
    filter_horizontal = ['assigned_employees']
    
    # Raw ID fields for foreign keys
    raw_id_fields = ('primary_assigned_employee', 'created_by')
    
    # Actions
    actions = [
        'mark_as_new',
        'mark_as_in_progress', 
        'mark_as_finished',
        'assign_to_team',
        'set_primary_employee',
        'export_projects'
    ]
    
    def status_display(self, obj):
        """Display status with colored badge"""
        color_map = {
            'new': '#AF52DE',
            'in_progress': '#FF9500',
            'finished': '#34C759',
        }
        color = color_map.get(obj.status, '#8E8E93')
        return format_html(
            '<span style="background: {}; color: white; padding: 2px 8px; '
            'border-radius: 4px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display_arabic()
        )
    status_display.short_description = 'الحالة'
    
    def assigned_team_display(self, obj):
        """Display assigned team with avatars and count"""
        employees = obj.assigned_employees.all()
        if not employees.exists():
            return format_html('<span style="color: #999; font-style: italic;">لا يوجد فريق</span>')
        
        count = employees.count()
        if count == 1:
            employee = employees.first()
            url = reverse('admin:employees_employee_change', args=[employee.pk])
            return format_html(
                '<a href="{}" style="text-decoration: none;">'
                '<div style="display: flex; align-items: center; gap: 0.5rem;">'
                '<div style="width: 24px; height: 24px; border-radius: 50%; background: #007AFF; '
                'color: white; display: flex; align-items: center; justify-content: center; '
                'font-size: 10px; font-weight: bold;">{}</div>'
                '<span style="font-weight: 500;">{}</span>'
                '</div></a>',
                url,
                employee.name[0].upper(),
                employee.name
            )
        elif count <= 3:
            # Show first few employees with avatars
            avatars_html = ''
            for i, employee in enumerate(employees[:3]):
                url = reverse('admin:employees_employee_change', args=[employee.pk])
                margin_style = f'margin-left: {-8 * i}px;' if i > 0 else ''
                avatars_html += format_html(
                    '<a href="{}" style="text-decoration: none;">'
                    '<div style="width: 24px; height: 24px; border-radius: 50%; background: #007AFF; '
                    'color: white; display: inline-flex; align-items: center; justify-content: center; '
                    'font-size: 10px; font-weight: bold; border: 2px solid white; {}z-index: {};"'
                    'title="{}">{}</div></a>',
                    url, margin_style, 10-i, employee.name, employee.name[0].upper()
                )
            return format_html(
                '<div style="display: flex; align-items: center; gap: 0.5rem;">'
                '<div style="display: flex; align-items: center;">{}</div>'
                '<span style="font-size: 11px; color: #666;">{} أعضاء</span>'
                '</div>',
                avatars_html, count
            )
        else:
            # Show first 2 + count indicator
            avatars_html = ''
            for i, employee in enumerate(employees[:2]):
                url = reverse('admin:employees_employee_change', args=[employee.pk])
                margin_style = f'margin-left: {-8 * i}px;' if i > 0 else ''
                avatars_html += format_html(
                    '<a href="{}" style="text-decoration: none;">'
                    '<div style="width: 24px; height: 24px; border-radius: 50%; background: #007AFF; '
                    'color: white; display: inline-flex; align-items: center; justify-content: center; '
                    'font-size: 10px; font-weight: bold; border: 2px solid white; {}z-index: {};"'
                    'title="{}">{}</div></a>',
                    url, margin_style, 10-i, employee.name, employee.name[0].upper()
                )
            
            # Add count indicator
            avatars_html += format_html(
                '<div style="width: 24px; height: 24px; border-radius: 50%; background: #8E8E93; '
                'color: white; display: inline-flex; align-items: center; justify-content: center; '
                'font-size: 10px; font-weight: bold; border: 2px solid white; margin-left: -8px; z-index: 1;"'
                'title="+{} أعضاء إضافيين">+{}</div>',
                count-2, count-2
            )
            
            return format_html(
                '<div style="display: flex; align-items: center; gap: 0.5rem;">'
                '<div style="display: flex; align-items: center;">{}</div>'
                '<span style="font-size: 11px; color: #666;">فريق من {} أعضاء</span>'
                '</div>',
                avatars_html, count
            )
    assigned_team_display.short_description = 'فريق العمل'
    
    def primary_employee_display(self, obj):
        """Display primary assigned employee"""
        if obj.primary_assigned_employee:
            url = reverse('admin:employees_employee_change', args=[obj.primary_assigned_employee.pk])
            return format_html(
                '<a href="{}" style="text-decoration: none;">'
                '<div style="display: flex; align-items: center; gap: 0.5rem;">'
                '<div style="width: 20px; height: 20px; border-radius: 50%; background: #34C759; '
                'color: white; display: flex; align-items: center; justify-content: center; '
                'font-size: 10px; font-weight: bold;">👑</div>'
                '<strong style="color: #34C759;">{}</strong>'
                '</div></a>',
                url,
                obj.primary_assigned_employee.name
            )
        elif obj.assigned_employees.exists():
            return format_html('<span style="color: #FF9500; font-style: italic;">لا يوجد قائد محدد</span>')
        else:
            return format_html('<span style="color: #999;">-</span>')
    primary_employee_display.short_description = 'القائد'
    
    def progress_display(self, obj):
        """Display progress bar"""
        progress = obj.progress_percentage()
        color_map = {
            'new': '#AF52DE',
            'in_progress': '#FF9500',
            'finished': '#34C759',
        }
        color = color_map.get(obj.status, '#8E8E93')
        
        return format_html(
            '<div style="width: 100px; background: #f0f0f0; border-radius: 10px; overflow: hidden;">'
            '<div style="width: {}%; height: 8px; background: {}; transition: width 0.3s;"></div>'
            '</div>'
            '<small style="color: #666; font-weight: bold;">{} %</small>',
            progress,
            color,
            progress
        )
    progress_display.short_description = 'التقدم'
    
    def due_date_display(self, obj):
        """Display due date with status indicator"""
        if not obj.due_date:
            return format_html('<span style="color: #999; font-style: italic;">غير محدد</span>')
        
        date_str = obj.due_date.strftime('%Y/%m/%d')
        
        if obj.is_overdue():
            return format_html(
                '<span style="color: #FF3B30; font-weight: bold;">{}</span><br>'
                '<small style="color: #FF3B30;">متأخر {} يوم</small>',
                date_str,
                abs(obj.days_remaining())
            )
        elif obj.days_remaining() <= 7:
            return format_html(
                '<span style="color: #FF9500; font-weight: bold;">{}</span><br>'
                '<small style="color: #FF9500;">باقي {} أيام</small>',
                date_str,
                obj.days_remaining()
            )
        else:
            return format_html(
                '<span>{}</span><br>'
                '<small style="color: #666;">باقي {} يوم</small>',
                date_str,
                obj.days_remaining()
            )
    due_date_display.short_description = 'تاريخ الانتهاء'
    
    def created_at_display(self, obj):
        """Display creation date"""
        return obj.created_at.strftime('%Y/%m/%d')
    created_at_display.short_description = 'تاريخ الإنشاء'
    
    def is_overdue_display(self, obj):
        """Display overdue status"""
        if obj.is_overdue():
            return format_html(
                '<span style="color: #FF3B30;">⚠️ متأخر</span>'
            )
        return format_html('<span style="color: #34C759;">✅ في الموعد</span>')
    is_overdue_display.short_description = 'الحالة الزمنية'
    
    def mark_as_new(self, request, queryset):
        """Mark selected projects as new"""
        updated = queryset.update(status='new')
        self.message_user(
            request,
            f'تم تحديث حالة {updated} مشروع إلى "جديد".'
        )
    mark_as_new.short_description = 'تحديد كـ "جديد"'
    
    def mark_as_in_progress(self, request, queryset):
        """Mark selected projects as in progress"""
        updated = queryset.update(status='in_progress')
        self.message_user(
            request,
            f'تم تحديث حالة {updated} مشروع إلى "قيد التنفيذ".'
        )
    mark_as_in_progress.short_description = 'تحديد كـ "قيد التنفيذ"'
    
    def mark_as_finished(self, request, queryset):
        """Mark selected projects as finished"""
        updated = queryset.update(status='finished')
        self.message_user(
            request,
            f'تم تحديث حالة {updated} مشروع إلى "مكتمل".'
        )
    mark_as_finished.short_description = 'تحديد كـ "مكتمل"'
    
    def assign_to_team(self, request, queryset):
        """Assign projects to a team (would need custom form)"""
        self.message_user(
            request,
            'لتعيين فرق متعددة لمشاريع، يرجى تحديد كل مشروع على حدة وتعديله.',
            level='warning'
        )
    assign_to_team.short_description = 'تعيين إلى فريق'
    
    def set_primary_employee(self, request, queryset):
        """Set primary employee for projects"""
        self.message_user(
            request,
            'لتحديد قائد فريق، يرجى تحديد كل مشروع على حدة وتعديله.',
            level='warning'
        )
    set_primary_employee.short_description = 'تحديد قائد الفريق'
    
    def export_projects(self, request, queryset):
        """Export selected projects to CSV"""
        import csv
        from django.http import HttpResponse
        from datetime import datetime
        
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="projects_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        # Add BOM for proper Arabic display in Excel
        response.write('\ufeff')
        
        writer = csv.writer(response)
        
        # Write header
        writer.writerow([
            'اسم المشروع',
            'الوصف',
            'الحالة',
            'عدد أعضاء الفريق',
            'فريق العمل',
            'القائد',
            'تاريخ الانتهاء',
            'منشئ المشروع',
            'تاريخ الإنشاء',
            'التقدم (%)',
            'متأخر؟'
        ])
        
        # Write data
        for project in queryset:
            team_members = ', '.join([emp.name for emp in project.assigned_employees.all()])
            primary_employee = project.primary_assigned_employee.name if project.primary_assigned_employee else 'غير محدد'
            
            writer.writerow([
                project.name,
                project.description,
                project.get_status_display_arabic(),
                project.assigned_employees_count,
                team_members or 'لا يوجد فريق',
                primary_employee,
                project.due_date.strftime('%Y-%m-%d') if project.due_date else 'غير محدد',
                project.created_by.name,
                project.created_at.strftime('%Y-%m-%d %H:%M'),
                project.progress_percentage(),
                'نعم' if project.is_overdue() else 'لا'
            ])
        
        return response
    export_projects.short_description = 'تصدير المشاريع المحددة إلى CSV'
    
    def get_queryset(self, request):
        """Optimize queryset with prefetch_related for many-to-many"""
        return super().get_queryset(request).prefetch_related(
            'assigned_employees', 
            'primary_assigned_employee', 
            'created_by'
        )
    
    def has_delete_permission(self, request, obj=None):
        """Check if user can delete project"""
        if obj and not obj.can_be_deleted():
            return False
        return super().has_delete_permission(request, obj)
    
    def delete_model(self, request, obj):
        """Override delete to check constraints"""
        if not obj.can_be_deleted():
            from django.contrib import messages
            messages.error(
                request, 
                f'لا يمكن حذف المشروع "{obj.name}" لأنه مرتبط ببيانات أخرى.'
            )
            return
        super().delete_model(request, obj)
    
    def save_model(self, request, obj, form, change):
        """Override save to add custom logic and validation"""
        # Set created_by if not provided (for new projects)
        if not change and not obj.created_by_id:
            obj.created_by = request.user
        
        # Validate primary employee is in assigned employees
        if obj.primary_assigned_employee and change:
            # We need to check after the many-to-many relationship is saved
            pass  # This will be handled in save_related
        
        super().save_model(request, obj, form, change)
        
        # Log the action
        if change:
            self.message_user(request, f'تم تحديث المشروع "{obj.name}" بنجاح.')
        else:
            self.message_user(request, f'تم إنشاء المشروع "{obj.name}" بنجاح.')
    
    def save_related(self, request, form, formsets, change):
        """Override to validate relationships after saving"""
        super().save_related(request, form, formsets, change)
        
        obj = form.instance
        
        # Validate that primary employee is in assigned employees
        if obj.primary_assigned_employee and obj.assigned_employees.exists():
            if obj.primary_assigned_employee not in obj.assigned_employees.all():
                from django.contrib import messages
                messages.warning(
                    request,
                    f'تحذير: القائد "{obj.primary_assigned_employee.name}" ليس من ضمن فريق العمل المُعيّن. '
                    f'يُنصح بإضافته إلى فريق العمل أو اختيار قائد آخر.'
                )
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Customize foreign key fields"""
        if db_field.name == "primary_assigned_employee":
            kwargs["queryset"] = Employee.objects.filter(is_active_employee=True).order_by('name')
            kwargs["help_text"] = "اختر الموظف الرئيسي المسؤول عن قيادة المشروع (يُفضل أن يكون من ضمن فريق العمل)"
        if db_field.name == "created_by":
            kwargs["queryset"] = Employee.objects.filter(is_active=True).order_by('name')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def formfield_for_manytomany(self, db_field, request, **kwargs):
        """Customize many-to-many fields"""
        if db_field.name == "assigned_employees":
            kwargs["queryset"] = Employee.objects.filter(is_active_employee=True).order_by('name')
            kwargs["help_text"] = "اختر جميع الموظفين المشاركين في المشروع"
        return super().formfield_for_manytomany(db_field, request, **kwargs)
    
    def get_form(self, request, obj=None, **kwargs):
        """Customize the form"""
        form = super().get_form(request, obj, **kwargs)
        
        # Add custom JavaScript for better UX
        form.Media.js = form.Media.js + ('admin/js/project_team_admin.js',)
        
        return form
    
    def response_change(self, request, obj):
        """Custom response after changing an object"""
        # Check team consistency and show helpful messages
        if obj.assigned_employees.exists():
            team_sections = set(obj.assigned_employees.values_list('section', flat=True))
            if len(team_sections) > 3:
                from django.contrib import messages
                messages.info(
                    request,
                    f'ملاحظة: الفريق يضم أعضاء من {len(team_sections)} أقسام مختلفة. '
                    f'قد يساعد في التنسيق تعيين قائد فريق من القسم الرئيسي.'
                )
            
            if not obj.primary_assigned_employee and obj.assigned_employees.count() > 1:
                from django.contrib import messages
                messages.info(
                    request,
                    'نصيحة: يُنصح بتحديد قائد فريق عند وجود أكثر من موظف واحد في المشروع.'
                )
        
        return super().response_change(request, obj)
    
    class Media:
        css = {
            'all': ('admin/css/project_admin.css',)
        }
        js = ('admin/js/project_admin.js',)