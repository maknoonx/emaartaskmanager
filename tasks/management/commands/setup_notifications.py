# Create this file as: tasks/management/commands/setup_notifications.py

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from tasks.notification_models import NotificationPreference, NotificationTemplate

Employee = get_user_model()

class Command(BaseCommand):
    help = 'Setup notification preferences and templates for all users'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--create-templates',
            action='store_true',
            help='Create default notification templates',
        )
        parser.add_argument(
            '--create-preferences',
            action='store_true',
            help='Create notification preferences for all users',
        )
    
    def handle(self, *args, **options):
        if options['create_templates']:
            self.create_default_templates()
        
        if options['create_preferences']:
            self.create_user_preferences()
        
        if not options['create_templates'] and not options['create_preferences']:
            # If no specific option, do both
            self.create_default_templates()
            self.create_user_preferences()
    
    def create_default_templates(self):
        """Create default notification templates"""
        templates = [
            {
                'name': 'تكليف مهمة جديدة',
                'template_type': 'task_assigned',
                'subject_template': 'تم تكليفك بمهمة جديدة - {task_name}',
                'html_template': '''
                <div style="font-family: Arial, sans-serif; direction: rtl; text-align: right;">
                    <h2>مرحباً {user_name}</h2>
                    <p>تم تكليفك بمهمة جديدة من قبل <strong>{assigner_name}</strong></p>
                    
                    <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="color: #007AFF;">تفاصيل المهمة:</h3>
                        <ul style="list-style: none; padding: 0;">
                            <li style="margin: 10px 0;"><strong>اسم المهمة:</strong> {task_name}</li>
                            <li style="margin: 10px 0;"><strong>المشروع:</strong> {project_name}</li>
                            <li style="margin: 10px 0;"><strong>تاريخ الاستحقاق:</strong> {due_date}</li>
                        </ul>
                    </div>
                    
                    <p>
                        <a href="{task_url}" style="background: #007AFF; color: white; padding: 10px 20px; 
                           text-decoration: none; border-radius: 5px;">عرض المهمة</a>
                    </p>
                    
                    <hr style="margin: 30px 0;">
                    <p style="color: #666; font-size: 12px;">
                        هذا إشعار تلقائي من نظام {site_name}<br>
                        لا تقم بالرد على هذا الإيميل
                    </p>
                </div>
                ''',
                'text_template': '''
مرحباً {user_name}

تم تكليفك بمهمة جديدة من قبل {assigner_name}

تفاصيل المهمة:
- اسم المهمة: {task_name}
- المشروع: {project_name}
- تاريخ الاستحقاق: {due_date}

لعرض المهمة: {task_url}

مع تحيات فريق {site_name}
                '''
            },
            {
                'name': 'إنجاز مهمة',
                'template_type': 'task_completed',
                'subject_template': 'تم إنجاز المهمة - {task_name}',
                'html_template': '''
                <div style="font-family: Arial, sans-serif; direction: rtl; text-align: right;">
                    <h2>مرحباً {user_name}</h2>
                    <p>تم إنجاز المهمة التي كلفت بها <strong>{completer_name}</strong></p>
                    
                    <div style="background: #e8f5e8; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #34C759;">
                        <h3 style="color: #34C759;">✅ المهمة مكتملة</h3>
                        <ul style="list-style: none; padding: 0;">
                            <li style="margin: 10px 0;"><strong>اسم المهمة:</strong> {task_name}</li>
                            <li style="margin: 10px 0;"><strong>المشروع:</strong> {project_name}</li>
                            <li style="margin: 10px 0;"><strong>تاريخ الإنجاز:</strong> {completion_date}</li>
                            <li style="margin: 10px 0;"><strong>أنجزت بواسطة:</strong> {completer_name}</li>
                        </ul>
                    </div>
                    
                    <p>
                        <a href="{task_url}" style="background: #34C759; color: white; padding: 10px 20px; 
                           text-decoration: none; border-radius: 5px;">عرض المهمة</a>
                    </p>
                    
                    <hr style="margin: 30px 0;">
                    <p style="color: #666; font-size: 12px;">
                        هذا إشعار تلقائي من نظام {site_name}<br>
                        لا تقم بالرد على هذا الإيميل
                    </p>
                </div>
                ''',
                'text_template': '''
مرحباً {user_name}

تم إنجاز المهمة التي كلفت بها {completer_name}

تفاصيل المهمة:
- اسم المهمة: {task_name}
- المشروع: {project_name}
- تاريخ الإنجاز: {completion_date}
- أنجزت بواسطة: {completer_name}

لعرض المهمة: {task_url}

مع تحيات فريق {site_name}
                '''
            },
            {
                'name': 'مهمة متأخرة',
                'template_type': 'task_overdue',
                'subject_template': '⚠️ تنبيه: مهمة متأخرة - {task_name}',
                'html_template': '''
                <div style="font-family: Arial, sans-serif; direction: rtl; text-align: right;">
                    <h2>مرحباً {user_name}</h2>
                    <div style="background: #fff3e0; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #FF9500;">
                        <h3 style="color: #FF9500;">⚠️ تنبيه: لديك مهمة متأخرة</h3>
                        <ul style="list-style: none; padding: 0;">
                            <li style="margin: 10px 0;"><strong>اسم المهمة:</strong> {task_name}</li>
                            <li style="margin: 10px 0;"><strong>المشروع:</strong> {project_name}</li>
                            <li style="margin: 10px 0;"><strong>تاريخ الاستحقاق:</strong> {due_date}</li>
                            <li style="margin: 10px 0; color: #FF3B30;"><strong>عدد الأيام المتأخرة:</strong> {days_overdue} يوم</li>
                        </ul>
                    </div>
                    
                    <p style="color: #FF3B30; font-weight: bold;">
                        يرجى إنجاز هذه المهمة في أقرب وقت ممكن
                    </p>
                    
                    <p>
                        <a href="{task_url}" style="background: #FF9500; color: white; padding: 10px 20px; 
                           text-decoration: none; border-radius: 5px;">عرض المهمة</a>
                    </p>
                    
                    <hr style="margin: 30px 0;">
                    <p style="color: #666; font-size: 12px;">
                        هذا إشعار تلقائي من نظام {site_name}<br>
                        لا تقم بالرد على هذا الإيميل
                    </p>
                </div>
                ''',
                'text_template': '''
مرحباً {user_name}

⚠️ تنبيه: لديك مهمة متأخرة

تفاصيل المهمة:
- اسم المهمة: {task_name}
- المشروع: {project_name}
- تاريخ الاستحقاق: {due_date}
- عدد الأيام المتأخرة: {days_overdue} يوم

يرجى إنجاز هذه المهمة في أقرب وقت ممكن

لعرض المهمة: {task_url}

مع تحيات فريق {site_name}
                '''
            },
            {
                'name': 'رسالة ترحيب',
                'template_type': 'welcome',
                'subject_template': 'مرحباً بك في {site_name}',
                'html_template': '''
                <div style="font-family: Arial, sans-serif; direction: rtl; text-align: right;">
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 8px; color: white; margin-bottom: 20px;">
                        <h1 style="margin: 0;">مرحباً بك في {site_name}</h1>
                        <p style="margin: 10px 0 0 0; opacity: 0.9;">نظام إدارة المهام والمشاريع</p>
                    </div>
                    
                    <h2>أهلاً وسهلاً {user_name}</h2>
                    <p>نرحب بك في نظام إدارة المهام الخاص بجمعية إعمار. يمكنك الآن:</p>
                    
                    <ul style="line-height: 2;">
                        <li>إدارة مهامك اليومية</li>
                        <li>متابعة المشاريع</li>
                        <li>التعاون مع فريق العمل</li>
                        <li>تتبع الإنجازات</li>
                    </ul>
                    
                    <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3>للبدء:</h3>
                        <p>
                            <a href="{login_url}" style="background: #007AFF; color: white; padding: 10px 20px; 
                               text-decoration: none; border-radius: 5px;">تسجيل الدخول إلى النظام</a>
                        </p>
                    </div>
                    
                    <hr style="margin: 30px 0;">
                    <p style="color: #666; font-size: 12px;">
                        إذا كان لديك أي استفسار، يرجى التواصل مع الدعم الفني<br>
                        مع تحيات فريق {site_name}
                    </p>
                </div>
                ''',
                'text_template': '''
مرحباً بك في {site_name}

أهلاً وسهلاً {user_name}

نرحب بك في نظام إدارة المهام الخاص بجمعية إعمار. يمكنك الآن:
- إدارة مهامك اليومية
- متابعة المشاريع
- التعاون مع فريق العمل
- تتبع الإنجازات

للبدء:
تسجيل الدخول إلى النظام: {login_url}

إذا كان لديك أي استفسار، يرجى التواصل مع الدعم الفني

مع تحيات فريق {site_name}
                '''
            }
        ]
        
        created_count = 0
        for template_data in templates:
            template, created = NotificationTemplate.objects.get_or_create(
                template_type=template_data['template_type'],
                defaults=template_data
            )
            if created:
                created_count += 1
                self.stdout.write(f"✓ Created template: {template.name}")
            else:
                self.stdout.write(f"- Template exists: {template.name}")
        
        self.stdout.write(
            self.style.SUCCESS(f"Setup complete. Created {created_count} new templates.")
        )
    
    def create_user_preferences(self):
        """Create notification preferences for all users"""
        users = Employee.objects.all()
        created_count = 0
        
        for user in users:
            preferences, created = NotificationPreference.objects.get_or_create(
                user=user,
                defaults={
                    'task_assigned_email': True,
                    'task_completed_email': True,
                    'task_overdue_email': True,
                    'project_assigned_email': True,
                    'email_notifications_enabled': True,
                    'daily_digest_enabled': False,
                }
            )
            if created:
                created_count += 1
                self.stdout.write(f"✓ Created preferences for: {user.email}")
            else:
                self.stdout.write(f"- Preferences exist for: {user.email}")
        
        self.stdout.write(
            self.style.SUCCESS(f"Setup complete. Created preferences for {created_count} users.")
        )