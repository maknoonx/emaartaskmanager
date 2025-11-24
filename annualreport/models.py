from django.db import models
from django.conf import settings
from django.utils import timezone

class Achievement(models.Model):
    """
    Model to store achievements for the annual report 2025
    """
    
    SECTION_CHOICES = [
        ('general', 'عام'),
        ('governance', 'حوكمة'),
        ('technical', 'تقني'),
        ('marketing', 'تسويق'),
        ('social_research', 'البحث الاجتماعي'),
        ('projects', 'المشاريع'),
        ('volunteering', 'التطوع'),
    ]
    
    # Required fields
    section = models.CharField(
        max_length=50,
        choices=SECTION_CHOICES,
        verbose_name='القسم الخاص بالإنجاز'
    )
    title = models.CharField(
        max_length=255,
        verbose_name='عنوان الإنجاز'
    )
    description = models.TextField(
        verbose_name='تفاصيل الإنجاز'
    )
    
    # Optional fields
    achievement_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاريخ الإنجاز'
    )
    display_in_report = models.BooleanField(
        default=True,
        verbose_name='عرض الإنجاز في التقرير السنوي'
    )
    
    # Metadata
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='achievements_created',
        verbose_name='المُنشئ'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاريخ آخر تحديث'
    )
    
    class Meta:
        verbose_name = 'إنجاز'
        verbose_name_plural = 'الإنجازات'
        ordering = ['-created_at']
        permissions = [
            ('can_view_all_achievements', 'يمكنه عرض جميع الإنجازات'),
            ('can_edit_all_achievements', 'يمكنه تعديل جميع الإنجازات'),
            ('can_delete_all_achievements', 'يمكنه حذف جميع الإنجازات'),
        ]
    
    def __str__(self):
        return f"{self.get_section_display()} - {self.title}"
    
    def get_section_display_arabic(self):
        """Get Arabic display name for section"""
        return dict(self.SECTION_CHOICES).get(self.section, self.section)
    
    def can_be_edited_by(self, user):
        """Check if user can edit this achievement"""
        if user.is_superuser:
            return True
        if user.has_perm('annualreport.can_edit_all_achievements'):
            return True
        return self.created_by == user
    
    def can_be_deleted_by(self, user):
        """Check if user can delete this achievement"""
        if user.is_superuser:
            return True
        if user.has_perm('annualreport.can_delete_all_achievements'):
            return True
        return self.created_by == user


class AchievementLink(models.Model):
    """
    Model to store multiple links/files for an achievement
    """
    
    achievement = models.ForeignKey(
        Achievement,
        on_delete=models.CASCADE,
        related_name='links',
        verbose_name='الإنجاز'
    )
    link_url = models.URLField(
        max_length=500,
        verbose_name='رابط المحتوى أو الملفات'
    )
    link_title = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='عنوان الرابط'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإضافة'
    )
    
    class Meta:
        verbose_name = 'رابط إنجاز'
        verbose_name_plural = 'روابط الإنجازات'
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.link_title or self.link_url}"