from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='NotificationPreference',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('task_assigned_email', models.BooleanField(default=True, verbose_name='إرسال إيميل عند التكليف بمهمة')),
                ('task_completed_email', models.BooleanField(default=True, verbose_name='إرسال إيميل عند إنجاز مهمة كلفت بها شخص')),
                ('task_overdue_email', models.BooleanField(default=True, verbose_name='إرسال إيميل للمهام المتأخرة')),
                ('project_assigned_email', models.BooleanField(default=True, verbose_name='إرسال إيميل عند التعيين في مشروع')),
                ('email_notifications_enabled', models.BooleanField(default=True, verbose_name='تفعيل الإشعارات عبر الإيميل')),
                ('daily_digest_enabled', models.BooleanField(default=False, verbose_name='ملخص يومي للمهام')),
                ('digest_time', models.TimeField(default=django.utils.timezone.now().time().replace(hour=9, minute=0), verbose_name='وقت إرسال الملخص اليومي')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='notification_preferences', to=settings.AUTH_USER_MODEL, verbose_name='الموظف')),
            ],
            options={
                'verbose_name': 'إعدادات الإشعارات',
                'verbose_name_plural': 'إعدادات الإشعارات',
            },
        ),
        migrations.CreateModel(
            name='NotificationTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='اسم القالب')),
                ('template_type', models.CharField(choices=[('task_assigned', 'تكليف مهمة'), ('task_completed', 'إنجاز مهمة'), ('task_overdue', 'مهمة متأخرة'), ('project_assigned', 'تعيين في مشروع'), ('daily_digest', 'ملخص يومي'), ('welcome', 'ترحيب')], max_length=20, unique=True, verbose_name='نوع القالب')),
                ('subject_template', models.CharField(help_text='يمكن استخدام متغيرات مثل {task_name}, {user_name}, {due_date}', max_length=255, verbose_name='قالب الموضوع')),
                ('html_template', models.TextField(help_text='قالب HTML للإيميل', verbose_name='قالب HTML')),
                ('text_template', models.TextField(help_text='قالب النص العادي للإيميل', verbose_name='قالب النص')),
                ('is_active', models.BooleanField(default=True, verbose_name='نشط')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'قالب إشعار',
                'verbose_name_plural': 'قوالب الإشعارات',
                'ordering': ['template_type'],
            },
        ),
        migrations.CreateModel(
            name='EmailNotificationLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notification_type', models.CharField(choices=[('task_assigned', 'تكليف مهمة'), ('task_completed', 'إنجاز مهمة'), ('task_overdue', 'مهمة متأخرة'), ('project_assigned', 'تعيين في مشروع'), ('daily_digest', 'ملخص يومي')], max_length=20, verbose_name='نوع الإشعار')),
                ('subject', models.CharField(max_length=255, verbose_name='الموضوع')),
                ('content', models.TextField(verbose_name='المحتوى')),
                ('status', models.CharField(choices=[('pending', 'معلق'), ('sent', 'مُرسل'), ('failed', 'فشل'), ('bounced', 'مرتد')], default='pending', max_length=10, verbose_name='الحالة')),
                ('error_message', models.TextField(blank=True, verbose_name='رسالة الخطأ')),
                ('sent_at', models.DateTimeField(blank=True, null=True, verbose_name='وقت الإرسال')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')),
                ('to_email', models.EmailField(max_length=254, verbose_name='البريد الإلكتروني')),
                ('from_email', models.EmailField(default='noreply@eemar.org', max_length=254, verbose_name='البريد المرسل')),
                ('read_at', models.DateTimeField(blank=True, null=True, verbose_name='وقت القراءة')),
                ('clicked_at', models.DateTimeField(blank=True, null=True, verbose_name='وقت النقر')),
                ('recipient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='received_notifications', to=settings.AUTH_USER_MODEL, verbose_name='المستقبل')),
                ('sender', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sent_notifications', to=settings.AUTH_USER_MODEL, verbose_name='المرسل')),
                ('task', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='email_notifications', to='tasks.task', verbose_name='المهمة')),
            ],
            options={
                'verbose_name': 'سجل إشعارات الإيميل',
                'verbose_name_plural': 'سجل إشعارات الإيميل',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='emailnotificationlog',
            index=models.Index(fields=['recipient', 'notification_type'], name='tasks_email_recipie_48b7e4_idx'),
        ),
        migrations.AddIndex(
            model_name='emailnotificationlog',
            index=models.Index(fields=['status', 'created_at'], name='tasks_email_status_a5c542_idx'),
        ),
        migrations.AddIndex(
            model_name='emailnotificationlog',
            index=models.Index(fields=['task'], name='tasks_email_task_id_89e2f1_idx'),
        ),
    ]