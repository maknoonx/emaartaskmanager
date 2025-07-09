# tasks/notification_models.py
# Create this new file for notification tracking

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Task

Employee = get_user_model()

class NotificationPreference(models.Model):
    """
    User preferences for notifications
    """
    NOTIFICATION_TYPES = [
        ('task_assigned', 'تم تكليفي بمهمة'),
        ('task_completed', 'تم إنجاز مهمة كلفت بها شخص'),
        ('task_overdue', 'مهمة متأخرة'),
        ('project_assigned', 'تم تعييني في مشروع'),
        ('project_updated', 'تحديث مشروع'),
    ]
    
    user = models.OneToOneField(
        Employee,
        on_delete=models.CASCADE,
        related_name='notification_preferences',
        verbose_name="الموظف"
    )
    
    # Email notification preferences
    task_assigned_email = models.BooleanField(
        default=True,
        verbose_name="إرسال إيميل عند التكليف بمهمة"
    )
    
    task_completed_email = models.BooleanField(
        default=True,
        verbose_name="إرسال إيميل عند إنجاز مهمة كلفت بها شخص"
    )
    
    task_overdue_email = models.BooleanField(
        default=True,
        verbose_name="إرسال إيميل للمهام المتأخرة"
    )
    
    project_assigned_email = models.BooleanField(
        default=True,
        verbose_name="إرسال إيميل عند التعيين في مشروع"
    )
    
    # General preferences
    email_notifications_enabled = models.BooleanField(
        default=True,
        verbose_name="تفعيل الإشعارات عبر الإيميل"
    )
    
    daily_digest_enabled = models.BooleanField(
        default=False,
        verbose_name="ملخص يومي للمهام"
    )
    
    digest_time = models.TimeField(
        default=timezone.now().time().replace(hour=9, minute=0),
        verbose_name="وقت إرسال الملخص اليومي"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "إعدادات الإشعارات"
        verbose_name_plural = "إعدادات الإشعارات"
    
    def __str__(self):
        return f"إعدادات الإشعارات - {self.user.name}"
    
    @classmethod
    def get_or_create_for_user(cls, user):
        """Get or create notification preferences for a user"""
        preferences, created = cls.objects.get_or_create(
            user=user,
            defaults={
                'task_assigned_email': True,
                'task_completed_email': True,
                'task_overdue_email': True,
                'project_assigned_email': True,
                'email_notifications_enabled': True,
            }
        )
        return preferences


class EmailNotificationLog(models.Model):
    """
    Log of sent email notifications
    """
    NOTIFICATION_TYPES = [
        ('task_assigned', 'تكليف مهمة'),
        ('task_completed', 'إنجاز مهمة'),
        ('task_overdue', 'مهمة متأخرة'),
        ('project_assigned', 'تعيين في مشروع'),
        ('daily_digest', 'ملخص يومي'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'معلق'),
        ('sent', 'مُرسل'),
        ('failed', 'فشل'),
        ('bounced', 'مرتد'),
    ]
    
    recipient = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='received_notifications',
        verbose_name="المستقبل"
    )
    
    sender = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_notifications',
        verbose_name="المرسل"
    )
    
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES,
        verbose_name="نوع الإشعار"
    )
    
    subject = models.CharField(
        max_length=255,
        verbose_name="الموضوع"
    )
    
    content = models.TextField(
        verbose_name="المحتوى"
    )
    
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='email_notifications',
        verbose_name="المهمة"
    )
    
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="الحالة"
    )
    
    error_message = models.TextField(
        blank=True,
        verbose_name="رسالة الخطأ"
    )
    
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="وقت الإرسال"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ الإنشاء"
    )
    
    # Email metadata
    to_email = models.EmailField(
        verbose_name="البريد الإلكتروني"
    )
    
    from_email = models.EmailField(
        default='noreply@eemar.org',
        verbose_name="البريد المرسل"
    )
    
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="وقت القراءة"
    )
    
    clicked_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="وقت النقر"
    )
    
    class Meta:
        verbose_name = "سجل إشعارات الإيميل"
        verbose_name_plural = "سجل إشعارات الإيميل"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'notification_type']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['task']),
        ]
    
    def __str__(self):
        return f"{self.get_notification_type_display()} - {self.recipient.name}"
    
    def mark_as_sent(self):
        """Mark notification as sent"""
        self.status = 'sent'
        self.sent_at = timezone.now()
        self.save(update_fields=['status', 'sent_at'])
    
    def mark_as_failed(self, error_message):
        """Mark notification as failed"""
        self.status = 'failed'
        self.error_message = error_message
        self.save(update_fields=['status', 'error_message'])
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.read_at:
            self.read_at = timezone.now()
            self.save(update_fields=['read_at'])
    
    def mark_as_clicked(self):
        """Mark notification as clicked"""
        if not self.clicked_at:
            self.clicked_at = timezone.now()
            self.save(update_fields=['clicked_at'])


class NotificationTemplate(models.Model):
    """
    Email templates for different notification types
    """
    TEMPLATE_TYPES = [
        ('task_assigned', 'تكليف مهمة'),
        ('task_completed', 'إنجاز مهمة'),
        ('task_overdue', 'مهمة متأخرة'),
        ('project_assigned', 'تعيين في مشروع'),
        ('daily_digest', 'ملخص يومي'),
        ('welcome', 'ترحيب'),
    ]
    
    name = models.CharField(
        max_length=100,
        verbose_name="اسم القالب"
    )
    
    template_type = models.CharField(
        max_length=20,
        choices=TEMPLATE_TYPES,
        unique=True,
        verbose_name="نوع القالب"
    )
    
    subject_template = models.CharField(
        max_length=255,
        verbose_name="قالب الموضوع",
        help_text="يمكن استخدام متغيرات مثل {task_name}, {user_name}, {due_date}"
    )
    
    html_template = models.TextField(
        verbose_name="قالب HTML",
        help_text="قالب HTML للإيميل"
    )
    
    text_template = models.TextField(
        verbose_name="قالب النص",
        help_text="قالب النص العادي للإيميل"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="نشط"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "قالب إشعار"
        verbose_name_plural = "قوالب الإشعارات"
        ordering = ['template_type']
    
    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"
    
    def render_subject(self, context):
        """Render subject with context variables"""
        return self.subject_template.format(**context)
    
    def render_html(self, context):
        """Render HTML template with context variables"""
        from django.template import Template, Context
        template = Template(self.html_template)
        return template.render(Context(context))
    
    def render_text(self, context):
        """Render text template with context variables"""
        from django.template import Template, Context
        template = Template(self.text_template)
        return template.render(Context(context))