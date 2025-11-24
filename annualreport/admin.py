from django.contrib import admin
from .models import Achievement, AchievementLink


class AchievementLinkInline(admin.TabularInline):
    model = AchievementLink
    extra = 1
    fields = ['link_url', 'link_title']


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'section',
        'achievement_date',
        'display_in_report',
        'created_by',
        'created_at'
    ]
    list_filter = [
        'section',
        'display_in_report',
        'achievement_date',
        'created_at'
    ]
    search_fields = [
        'title',
        'description',
        'created_by__name',
        'created_by__username'
    ]
    readonly_fields = ['created_at', 'updated_at']
    inlines = [AchievementLinkInline]
    
    fieldsets = (
        ('معلومات الإنجاز', {
            'fields': ('section', 'title', 'description', 'achievement_date')
        }),
        ('الإعدادات', {
            'fields': ('display_in_report', 'created_by')
        }),
        ('معلومات إضافية', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(AchievementLink)
class AchievementLinkAdmin(admin.ModelAdmin):
    list_display = ['achievement', 'link_title', 'link_url', 'created_at']
    list_filter = ['created_at']
    search_fields = ['link_title', 'link_url', 'achievement__title']