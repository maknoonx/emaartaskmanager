# tasks/notification_models.py
# تحديث نموذج تفضيلات الإشعارات لإضافة تذكيرات المواعيد النهائية

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

Employee = get_user_model()

class NotificationPreference(models.Model):
    """
    تفضيلات الإشعارات للموظفين
    """
    user = models.OneToOneField(
        Employee, 
        on_delete=models.CASCADE,
        related_name='notification_preferences',
        verbose_name='الموظف'
    )
    
    # إعدادات عامة للإشعارات
    email_notifications_enabled = models.BooleanField(
        default=True,
        verbose_name='تفعيل إشعارات البريد الإلكتروني'
    )
    
    # إشعارات المهام الأساسية (الموجودة مسبقاً)
    task_assigned_email = models.BooleanField(
        default=True,
        verbose_name='إشعار تكليف مهمة جديدة'
    )
    
    task_completed_email = models.BooleanField(
        default=True,
        verbose_name='إشعار إنجاز مهمة'
    )
    
    task_overdue_email = models.BooleanField(
        default=True,
        verbose_name='إشعار المهام المتأخرة'
    )
    
    # إشعارات تذكيرات المواعيد النهائية (جديدة)
    task_deadline_reminders = models.BooleanField(
        default=True,
        verbose_name='تذكيرات مواعيد انتهاء المهام'
    )
    
    deadline_3_days_reminder = models.BooleanField(
        default=True,
        verbose_name='تذكير قبل 3 أيام من الانتهاء'
    )
    
    deadline_1_day_reminder = models.BooleanField(
        default=True,
        verbose_name='تذكير قبل يوم واحد من الانتهاء'
    )
    
    deadline_same_day_reminder = models.BooleanField(
        default=True,
        verbose_name='تذكير في نفس يوم الانتهاء'
    )
    
    # إعدادات متقدمة لتذكيرات المواعيد
    high_priority_task_reminders = models.BooleanField(
        default=True,
        verbose_name='تذكيرات إضافية للمهام عالية الأولوية'
    )
    
    weekend_reminders_enabled = models.BooleanField(
        default=False,
        verbose_name='إرسال التذكيرات في نهاية الأسبوع'
    )
    
    # توقيت إرسال التذكيرات
    preferred_reminder_time = models.TimeField(
        default=timezone.now().time().replace(hour=9, minute=0, second=0, microsecond=0),
        verbose_name='الوقت المفضل لاستلام التذكيرات'
    )
    
    # إشعارات المشاريع (الموجودة مسبقاً)
    project_assigned_email = models.BooleanField(
        default=True,
        verbose_name='إشعار تكليف مشروع جديد'
    )
    
    # الملخص اليومي (الموجود مسبقاً)
    daily_digest_enabled = models.BooleanField(
        default=True,
        verbose_name='تفعيل الملخص اليومي'
    )
    
    digest_time = models.TimeField(
        default=timezone.now().time().replace(hour=8, minute=30, second=0, microsecond=0),
        verbose_name='وقت إرسال الملخص اليومي'
    )
    
    # إعدادات تكرار التذكيرات
    max_reminders_per_task = models.PositiveIntegerField(
        default=3,
        verbose_name='عدد التذكيرات القصوى لكل مهمة يومياً'
    )
    
    reminder_interval_hours = models.PositiveIntegerField(
        default=4,
        verbose_name='الفاصل الزمني بين التذكيرات (ساعات)'
    )
    
    # تواريخ التتبع
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')
    
    class Meta:
        verbose_name = 'تفضيلات الإشعارات'
        verbose_name_plural = 'تفضيلات الإشعارات'
        db_table = 'notification_preferences'
    
    def __str__(self):
        return f'تفضيلات إشعارات {self.user.name}'
    
    @classmethod
    def get_or_create_for_user(cls, user):
        """
        الحصول على تفضيلات المستخدم أو إنشاؤها إذا لم تكن موجودة
        """
        preferences, created = cls.objects.get_or_create(
            user=user,
            defaults={
                'email_notifications_enabled': True,
                'task_assigned_email': True,
                'task_completed_email': True,
                'task_overdue_email': True,
                'task_deadline_reminders': True,
                'deadline_3_days_reminder': True,
                'deadline_1_day_reminder': True,
                'deadline_same_day_reminder': True,
                'high_priority_task_reminders': True,
                'weekend_reminders_enabled': False,
                'project_assigned_email': True,
                'daily_digest_enabled': True,
                'max_reminders_per_task': 3,
                'reminder_interval_hours': 4,
            }
        )
        return preferences
    
    def should_send_deadline_reminder(self, days_remaining):
        """
        تحديد ما إذا كان يجب إرسال تذكير حسب عدد الأيام المتبقية
        """
        if not self.email_notifications_enabled or not self.task_deadline_reminders:
            return False
        
        if days_remaining == 3:
            return self.deadline_3_days_reminder
        elif days_remaining == 1:
            return self.deadline_1_day_reminder
        elif days_remaining == 0:
            return self.deadline_same_day_reminder
        
        return False
    
    def is_weekend_reminder_allowed(self):
        """
        تحديد ما إذا كان مسموحاً بإرسال التذكيرات في نهاية الأسبوع
        """
        return self.weekend_reminders_enabled


class EmailNotificationLog(models.Model):
    """
    سجل إرسال الإشعارات عبر البريد الإلكتروني
    """
    NOTIFICATION_TYPES = [
        ('task_assigned', 'تكليف مهمة'),
        ('task_completed', 'إنجاز مهمة'),
        ('task_overdue', 'مهمة متأخرة'),
        ('task_due_in_3_days', 'مهمة تنتهي خلال 3 أيام'),
        ('task_due_tomorrow', 'مهمة تنتهي غداً'),
        ('task_due_today', 'مهمة تنتهي اليوم'),
        ('high_priority_reminder', 'تذكير مهمة عالية الأولوية'),
        ('project_assigned', 'تكليف مشروع'),
        ('daily_digest', 'الملخص اليومي'),
        ('weekly_report', 'التقرير الأسبوعي'),
        ('welcome', 'رسالة ترحيب'),
    ]
    
    STATUS_CHOICES = [
        ('sent', 'تم الإرسال'),
        ('failed', 'فشل الإرسال'),
        ('pending', 'في انتظار الإرسال'),
        ('cancelled', 'ملغي'),
    ]
    
    recipient = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='notification_logs',
        verbose_name='المستلم'
    )
    
    notification_type = models.CharField(
        max_length=50,
        choices=NOTIFICATION_TYPES,
        verbose_name='نوع الإشعار'
    )
    
    subject = models.CharField(
        max_length=200,
        verbose_name='موضوع الرسالة'
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='حالة الإرسال'
    )
    
    # ربط المهمة أو المشروع إذا كان متاحاً
    task = models.ForeignKey(
        'Task',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notification_logs',
        verbose_name='المهمة المرتبطة'
    )
    
    project = models.ForeignKey(
        'Project',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notification_logs',
        verbose_name='المشروع المرتبط'
    )
    
    # تفاصيل إضافية
    sender = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_notifications',
        verbose_name='المرسل'
    )
    
    error_message = models.TextField(
        blank=True,
        null=True,
        verbose_name='رسالة الخطأ'
    )
    
    email_provider_response = models.TextField(
        blank=True,
        null=True,
        verbose_name='استجابة مزود البريد الإلكتروني'
    )
    
    # معلومات التوقيت
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء'
    )
    
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاريخ الإرسال'
    )
    
    # معلومات إضافية للتتبع
    retry_count = models.PositiveIntegerField(
        default=0,
        verbose_name='عدد محاولات الإعادة'
    )
    
    is_reminder = models.BooleanField(
        default=False,
        verbose_name='هل هو تذكير'
    )
    
    reminder_sequence = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='تسلسل التذكير'
    )
    
    class Meta:
        verbose_name = 'سجل إشعار البريد الإلكتروني'
        verbose_name_plural = 'سجلات إشعارات البريد الإلكتروني'
        db_table = 'email_notification_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'notification_type']),
            models.Index(fields=['created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['task']),
        ]
    
    def __str__(self):
        return f'{self.get_notification_type_display()} - {self.recipient.name} - {self.status}'
    
    def mark_as_sent(self):
        """وضع علامة كمرسل بنجاح"""
        self.status = 'sent'
        self.sent_at = timezone.now()
        self.save(update_fields=['status', 'sent_at'])
    
    def mark_as_failed(self, error_message):
        """وضع علامة كفاشل مع رسالة الخطأ"""
        self.status = 'failed'
        self.error_message = error_message
        self.save(update_fields=['status', 'error_message'])
    
    def increment_retry_count(self):
        """زيادة عداد محاولات الإعادة"""
        self.retry_count += 1
        self.save(update_fields=['retry_count'])


class TaskReminderTracker(models.Model):
    """
    تتبع التذكيرات المرسلة لكل مهمة لتجنب الإرسال المتكرر
    """
    task = models.ForeignKey(
        'Task',
        on_delete=models.CASCADE,
        related_name='reminder_trackers',
        verbose_name='المهمة'
    )
    
    user = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='task_reminders',
        verbose_name='المستخدم'
    )
    
    # أنواع التذكيرات المرسلة
    three_days_reminder_sent = models.BooleanField(
        default=False,
        verbose_name='تم إرسال تذكير 3 أيام'
    )
    
    one_day_reminder_sent = models.BooleanField(
        default=False,
        verbose_name='تم إرسال تذكير يوم واحد'
    )
    
    same_day_reminder_sent = models.BooleanField(
        default=False,
        verbose_name='تم إرسال تذكير نفس اليوم'
    )
    
    # تواريخ الإرسال
    three_days_reminder_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاريخ تذكير 3 أيام'
    )
    
    one_day_reminder_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاريخ تذكير يوم واحد'
    )
    
    same_day_reminder_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاريخ تذكير نفس اليوم'
    )
    
    # عدد التذكيرات المرسلة اليوم
    daily_reminder_count = models.PositiveIntegerField(
        default=0,
        verbose_name='عدد التذكيرات اليومية'
    )
    
    last_reminder_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاريخ آخر تذكير'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'متتبع تذكيرات المهمة'
        verbose_name_plural = 'متتبعات تذكيرات المهام'
        db_table = 'task_reminder_trackers'
        unique_together = ['task', 'user']
        indexes = [
            models.Index(fields=['task', 'user']),
            models.Index(fields=['last_reminder_date']),
        ]
    
    def __str__(self):
        return f'تتبع تذكيرات {self.task.name} - {self.user.name}'
    
    def can_send_reminder(self, reminder_type, max_daily_reminders=3):
        """
        تحديد ما إذا كان يمكن إرسال تذكير معين
        """
        today = timezone.now().date()
        
        # إعادة تعيين العداد اليومي إذا كان يوم جديد
        if self.last_reminder_date != today:
            self.daily_reminder_count = 0
            self.last_reminder_date = today
            self.save(update_fields=['daily_reminder_count', 'last_reminder_date'])
        
        # فحص الحد الأقصى للتذكيرات اليومية
        if self.daily_reminder_count >= max_daily_reminders:
            return False
        
        # فحص نوع التذكير المحدد
        if reminder_type == 'three_days' and self.three_days_reminder_sent:
            return False
        elif reminder_type == 'one_day' and self.one_day_reminder_sent:
            return False
        elif reminder_type == 'same_day' and self.same_day_reminder_sent:
            return False
        
        return True
    
    def mark_reminder_sent(self, reminder_type):
        """
        وضع علامة على إرسال تذكير معين
        """
        now = timezone.now()
        today = now.date()
        
        if reminder_type == 'three_days':
            self.three_days_reminder_sent = True
            self.three_days_reminder_date = now
        elif reminder_type == 'one_day':
            self.one_day_reminder_sent = True
            self.one_day_reminder_date = now
        elif reminder_type == 'same_day':
            self.same_day_reminder_sent = True
            self.same_day_reminder_date = now
        
        # تحديث العداد اليومي
        if self.last_reminder_date != today:
            self.daily_reminder_count = 1
        else:
            self.daily_reminder_count += 1
        
        self.last_reminder_date = today
        self.save()
    
    @classmethod
    def get_or_create_tracker(cls, task, user):
        """
        الحصول على متتبع التذكيرات أو إنشاؤه
        """
        tracker, created = cls.objects.get_or_create(
            task=task,
            user=user,
            defaults={
                'daily_reminder_count': 0,
            }
        )
        return tracker