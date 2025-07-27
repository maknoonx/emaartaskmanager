# tasks/enhanced_deadline_tasks.py
# المهام المحسّنة لتذكيرات مواعيد انتهاء المهام مع تتبع الإرسال

from celery import shared_task
from django.utils import timezone
from datetime import timedelta, date, datetime
from django.contrib.auth import get_user_model
from django.db.models import Q
import logging

Employee = get_user_model()
logger = logging.getLogger('notifications')

@shared_task
def send_enhanced_deadline_reminders():
    """
    إرسال تذكيرات محسّنة للمهام قريبة الانتهاء مع تتبع التكرار
    """
    from .models import Task
    from .notification_models import TaskReminderTracker, NotificationPreference
    from .services.notification_service import get_notification_service
    
    notification_service = get_notification_service()
    today = timezone.now().date()
    
    # احصائيات الإرسال
    stats = {
        'total_tasks_checked': 0,
        'reminders_sent': 0,
        'reminders_skipped': 0,
        'errors': 0
    }
    
    # المهام النشطة التي لها تاريخ انتهاء
    active_tasks = Task.objects.filter(
        status__in=['new', 'in_progress'],
        due_date__isnull=False
    ).select_related('created_by', 'assigned_to', 'project')
    
    stats['total_tasks_checked'] = active_tasks.count()
    
    for task in active_tasks:
        try:
            days_remaining = (task.due_date - today).days
            
            # تحديد نوع التذكير المطلوب
            reminder_type = None
            if days_remaining == 3:
                reminder_type = 'three_days'
            elif days_remaining == 1:
                reminder_type = 'one_day'
            elif days_remaining == 0:
                reminder_type = 'same_day'
            
            if reminder_type:
                # إرسال تذكيرات لمنشئ المهمة والمُسند إليه
                recipients = get_task_recipients(task)
                
                for recipient in recipients:
                    if send_deadline_reminder_to_user(task, recipient, reminder_type, days_remaining):
                        stats['reminders_sent'] += 1
                    else:
                        stats['reminders_skipped'] += 1
                        
        except Exception as e:
            logger.error(f"خطأ في معالجة المهمة {task.id}: {str(e)}")
            stats['errors'] += 1
    
    logger.info(f"إحصائيات تذكيرات المواعيد: {stats}")
    return stats

def get_task_recipients(task):
    """
    الحصول على قائمة مستلمي التذكيرات للمهمة
    """
    recipients = set()
    
    # إضافة منشئ المهمة
    if task.created_by:
        recipients.add(task.created_by)
    
    # إضافة المُسند إليه إذا كان مختلفاً عن المنشئ
    if task.assigned_to and task.assigned_to != task.created_by:
        recipients.add(task.assigned_to)
    
    return list(recipients)

def send_deadline_reminder_to_user(task, user, reminder_type, days_remaining):
    """
    إرسال تذكير مواعيد انتهاء مهمة لمستخدم محدد
    """
    from .notification_models import TaskReminderTracker, NotificationPreference
    from .services.notification_service import get_notification_service
    
    try:
        # فحص تفضيلات المستخدم
        preferences = NotificationPreference.get_or_create_for_user(user)
        
        if not preferences.should_send_deadline_reminder(days_remaining):
            logger.debug(f"تذكير {reminder_type} معطل للمستخدم {user.email}")
            return False
        
        # فحص ما إذا كان يوم نهاية أسبوع
        if is_weekend() and not preferences.is_weekend_reminder_allowed():
            logger.debug(f"تذكيرات نهاية الأسبوع معطلة للمستخدم {user.email}")
            return False
        
        # الحصول على متتبع التذكيرات
        tracker = TaskReminderTracker.get_or_create_tracker(task, user)
        
        # فحص إمكانية إرسال التذكير
        if not tracker.can_send_reminder(reminder_type, preferences.max_reminders_per_task):
            logger.debug(f"تم تجاوز حد التذكيرات للمستخدم {user.email} والمهمة {task.id}")
            return False
        
        # إرسال التذكير
        notification_service = get_notification_service()
        success = send_enhanced_deadline_notification(
            task, user, reminder_type, days_remaining, notification_service
        )
        
        if success:
            # تحديث متتبع التذكيرات
            tracker.mark_reminder_sent(reminder_type)
            
            # تسجيل في سجل الإشعارات
            log_deadline_reminder(task, user, reminder_type, 'sent')
            
            logger.info(f"تم إرسال تذكير {reminder_type} للمستخدم {user.email} للمهمة {task.id}")
            return True
        else:
            log_deadline_reminder(task, user, reminder_type, 'failed')
            return False
            
    except Exception as e:
        logger.error(f"خطأ في إرسال تذكير للمستخدم {user.email} للمهمة {task.id}: {str(e)}")
        log_deadline_reminder(task, user, reminder_type, 'failed', str(e))
        return False

def send_enhanced_deadline_notification(task, user, reminder_type, days_remaining, notification_service):
    """
    إرسال إشعار تذكير محسّن
    """
    try:
        # تحديد نوع الإشعار
        notification_type_map = {
            'three_days': 'task_due_in_3_days',
            'one_day': 'task_due_tomorrow',
            'same_day': 'task_due_today'
        }
        
        notification_type = notification_type_map.get(reminder_type)
        
        # إعداد السياق
        context = create_deadline_context(task, user, days_remaining)
        
        # تحديد العنوان والمحتوى
        subject, html_content, text_content = create_deadline_content(
            reminder_type, context, days_remaining
        )
        
        # إرسال الإيميل
        return notification_service._send_email(
            recipient=user,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            notification_type=notification_type,
            task=task
        )
        
    except Exception as e:
        logger.error(f"خطأ في إرسال الإشعار: {str(e)}")
        return False

def create_deadline_context(task, user, days_remaining):
    """
    إنشاء سياق شامل للتذكير
    """
    from .services.notification_service import get_notification_service
    
    notification_service = get_notification_service()
    
    # حساب معلومات إضافية
    task_progress = calculate_task_progress(task)
    urgency_level = get_urgency_level(days_remaining)
    
    return {
        'task': task,
        'user': user,
        'days_remaining': days_remaining,
        'task_name': task.name,
        'project_name': task.project.name if task.project else 'غير محدد',
        'due_date': task.due_date.strftime('%Y-%m-%d'),
        'due_date_formatted': task.due_date.strftime('%A، %d %B %Y'),
        'user_name': user.name,
        'creator_name': task.created_by.name if task.created_by else '',
        'assignee_name': task.assigned_to.name if task.assigned_to else '',
        'task_url': f"{notification_service.site_url}/tasks/{task.pk}/",
        'site_name': notification_service.site_name,
        'site_url': notification_service.site_url,
        'task_progress': task_progress,
        'urgency_level': urgency_level,
        'is_weekend': is_weekend(),
        'current_time': timezone.now().strftime('%H:%M'),
        'current_date': timezone.now().strftime('%Y-%m-%d'),
        'task_priority': getattr(task, 'priority', 'متوسطة'),
        'task_status_display': task.get_status_display() if hasattr(task, 'get_status_display') else task.status,
    }

def calculate_task_progress(task):
    """
    حساب تقدم المهمة (يمكن تخصيصه حسب نموذج المهمة)
    """
    if hasattr(task, 'progress'):
        return task.progress
    elif task.status == 'new':
        return 0
    elif task.status == 'in_progress':
        return 50
    elif task.status == 'finished':
        return 100
    else:
        return 0

def get_urgency_level(days_remaining):
    """
    تحديد مستوى الإلحاح حسب الأيام المتبقية
    """
    if days_remaining <= 0:
        return 'عاجل جداً'
    elif days_remaining == 1:
        return 'عاجل'
    elif days_remaining <= 3:
        return 'مهم'
    else:
        return 'عادي'

def is_weekend():
    """
    فحص ما إذا كان اليوم نهاية أسبوع
    """
    today = timezone.now().weekday()
    # 4 = الجمعة، 5 = السبت (في التقويم الإسلامي)
    return today in [4, 5]

def create_deadline_content(reminder_type, context, days_remaining):
    """
    إنشاء محتوى التذكير حسب النوع
    """
    if reminder_type == 'three_days':
        return create_3_days_content(context)
    elif reminder_type == 'one_day':
        return create_1_day_content(context)
    elif reminder_type == 'same_day':
        return create_same_day_content(context)
    else:
        return create_default_content(context)

def create_3_days_content(context):
    """محتوى تذكير 3 أيام"""
    subject = f"تذكير: تنتهي مهمتك بعد 3 أيام - {context['task_name']}"
    
    html_content = f"""
    <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; direction: rtl; text-align: right; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px 10px 0 0;">
            <h2 style="margin: 0; font-size: 24px;">📅 تذكير بموعد انتهاء المهمة</h2>
        </div>
        
        <div style="background: white; padding: 30px; border-radius: 0 0 10px 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <h3 style="color: #4a5568; margin-top: 0;">مرحباً {context['user_name']}،</h3>
            
            <div style="background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; border-radius: 5px;">
                <p style="margin: 0; font-weight: bold; color: #856404;">
                    🔔 تذكير ودود: تنتهي مهمتك بعد 3 أيام
                </p>
            </div>
            
            <p style="color: #4a5568; line-height: 1.6;">
                نود تذكيرك بأن لديك مهمة ستنتهي خلال 3 أيام. لا يزال لديك وقت كافٍ لإنجازها بشكل ممتاز!
            </p>
            
            <div style="background: #f7fafc; padding: 20px; border-radius: 8px; margin: 25px 0;">
                <h4 style="color: #2d3748; margin-top: 0; display: flex; align-items: center;">
                    📋 تفاصيل المهمة
                </h4>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 8px 0; color: #4a5568; font-weight: bold; width: 30%;">اسم المهمة:</td>
                        <td style="padding: 8px 0; color: #2d3748;">{context['task_name']}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; color: #4a5568; font-weight: bold;">المشروع:</td>
                        <td style="padding: 8px 0; color: #2d3748;">{context['project_name']}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; color: #4a5568; font-weight: bold;">تاريخ الانتهاء:</td>
                        <td style="padding: 8px 0; color: #e53e3e; font-weight: bold;">{context['due_date_formatted']}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; color: #4a5568; font-weight: bold;">المتبقي:</td>
                        <td style="padding: 8px 0; color: #d69e2e; font-weight: bold;">3 أيام</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; color: #4a5568; font-weight: bold;">مستوى الإلحاح:</td>
                        <td style="padding: 8px 0; color: #38a169;">{context['urgency_level']}</td>
                    </tr>
                </table>
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{context['task_url']}" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 25px; font-weight: bold; display: inline-block; box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);">
                    🚀 عرض المهمة والعمل عليها
                </a>
            </div>
            
            <div style="background: #e6fffa; border: 1px solid #81e6d9; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <p style="margin: 0; color: #234e52;">
                    💡 <strong>نصيحة:</strong> يمكنك تقسيم المهمة إلى مهام فرعية أصغر لإنجازها بكفاءة أكبر.
                </p>
            </div>
            
            <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 30px 0;">
            
            <p style="color: #718096; font-size: 14px; text-align: center;">
                مع تحيات فريق {context['site_name']}<br>
                <small>هذا إشعار تلقائي، يرجى عدم الرد على هذا البريد الإلكتروني.</small>
            </p>
        </div>
    </div>
    """
    
    text_content = f"""
مرحباً {context['user_name']}

📅 تذكير: تنتهي مهمتك بعد 3 أيام

نود تذكيرك بأن لديك مهمة ستنتهي خلال 3 أيام. لا يزال لديك وقت كافٍ لإنجازها!

تفاصيل المهمة:
- اسم المهمة: {context['task_name']}
- المشروع: {context['project_name']}
- تاريخ الانتهاء: {context['due_date_formatted']}
- المتبقي: 3 أيام
- مستوى الإلحاح: {context['urgency_level']}

لعرض المهمة: {context['task_url']}

💡 نصيحة: يمكنك تقسيم المهمة إلى مهام فرعية أصغر لإنجازها بكفاءة أكبر.

مع تحيات فريق {context['site_name']}
---
هذا إشعار تلقائي، يرجى عدم الرد على هذا البريد الإلكتروني.
    """
    
    return subject, html_content, text_content

def create_1_day_content(context):
    """محتوى تذكير يوم واحد"""
    subject = f"⚠️ تنبيه: تنتهي مهمتك غداً - {context['task_name']}"
    
    html_content = f"""
    <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; direction: rtl; text-align: right; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; padding: 20px; border-radius: 10px 10px 0 0;">
            <h2 style="margin: 0; font-size: 24px;">⏰ تنبيه مهم: مهمة قريبة الانتهاء</h2>
        </div>
        
        <div style="background: white; padding: 30px; border-radius: 0 0 10px 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <h3 style="color: #4a5568; margin-top: 0;">مرحباً {context['user_name']}،</h3>
            
            <div style="background: #fed7d7; border-left: 4px solid #e53e3e; padding: 15px; margin: 20px 0; border-radius: 5px;">
                <p style="margin: 0; font-weight: bold; color: #9b2c2c;">
                    ⚠️ تنبيه مهم: تنتهي مهمتك غداً!
                </p>
            </div>
            
            <p style="color: #4a5568; line-height: 1.6; font-size: 16px;">
                <strong>هذا تذكير عاجل</strong> بأن لديك مهمة ستنتهي غداً (خلال 24 ساعة). 
                يرجى التأكد من إنجازها في الوقت المحدد.
            </p>
            
            <div style="background: #f7fafc; padding: 20px; border-radius: 8px; margin: 25px 0; border: 2px solid #fed7d7;">
                <h4 style="color: #2d3748; margin-top: 0; display: flex; align-items: center;">
                    📋 تفاصيل المهمة العاجلة
                </h4>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 8px 0; color: #4a5568; font-weight: bold; width: 30%;">اسم المهمة:</td>
                        <td style="padding: 8px 0; color: #2d3748; font-weight: bold;">{context['task_name']}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; color: #4a5568; font-weight: bold;">المشروع:</td>
                        <td style="padding: 8px 0; color: #2d3748;">{context['project_name']}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; color: #4a5568; font-weight: bold;">تاريخ الانتهاء:</td>
                        <td style="padding: 8px 0; color: #e53e3e; font-weight: bold; font-size: 16px;">{context['due_date_formatted']}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; color: #4a5568; font-weight: bold;">المتبقي:</td>
                        <td style="padding: 8px 0; color: #e53e3e; font-weight: bold; font-size: 16px;">يوم واحد فقط!</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; color: #4a5568; font-weight: bold;">مستوى الإلحاح:</td>
                        <td style="padding: 8px 0; color: #e53e3e; font-weight: bold;">{context['urgency_level']}</td>
                    </tr>
                </table>
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{context['task_url']}" style="background: linear-gradient(135deg, #e53e3e 0%, #9b2c2c 100%); color: white; padding: 18px 35px; text-decoration: none; border-radius: 25px; font-weight: bold; display: inline-block; box-shadow: 0 4px 15px rgba(229, 62, 62, 0.4); font-size: 16px;">
                    🚨 عرض المهمة فوراً
                </a>
            </div>
            
            <div style="background: #fed7d7; border: 1px solid #e53e3e; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <p style="margin: 0; color: #9b2c2c; font-weight: bold; text-align: center;">
                    ⚠️ يرجى إنجاز هذه المهمة اليوم لتجنب التأخير!
                </p>
            </div>
            
            <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 30px 0;">
            
            <p style="color: #718096; font-size: 14px; text-align: center;">
                مع تحيات فريق {context['site_name']}<br>
                <small>هذا إشعار تلقائي، يرجى عدم الرد على هذا البريد الإلكتروني.</small>
            </p>
        </div>
    </div>
    """
    
    text_content = f"""
مرحباً {context['user_name']}

⚠️ تنبيه مهم: تنتهي مهمتك غداً!

هذا تذكير عاجل بأن لديك مهمة ستنتهي غداً (خلال 24 ساعة).

تفاصيل المهمة العاجلة:
- اسم المهمة: {context['task_name']}
- المشروع: {context['project_name']}
- تاريخ الانتهاء: {context['due_date_formatted']}
- المتبقي: يوم واحد فقط!
- مستوى الإلحاح: {context['urgency_level']}

لعرض المهمة: {context['task_url']}

⚠️ يرجى إنجاز هذه المهمة اليوم لتجنب التأخير!

مع تحيات فريق {context['site_name']}
---
هذا إشعار تلقائي، يرجى عدم الرد على هذا البريد الإلكتروني.
    """
    
    return subject, html_content, text_content

def create_same_day_content(context):
    """محتوى المهام المستحقة اليوم"""
    subject = f"🚨 عاجل جداً: مهمتك تنتهي اليوم - {context['task_name']}"
    
    html_content = f"""
    <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; direction: rtl; text-align: right; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%); color: white; padding: 25px; border-radius: 10px 10px 0 0; animation: pulse 2s infinite;">
            <h2 style="margin: 0; font-size: 26px; text-align: center;">🚨 تنبيه عاجل جداً</h2>
        </div>
        
        <div style="background: white; padding: 30px; border-radius: 0 0 10px 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <h3 style="color: #4a5568; margin-top: 0;">مرحباً {context['user_name']}،</h3>
            
            <div style="background: #feb2b2; border: 3px solid #e53e3e; padding: 20px; margin: 20px 0; border-radius: 8px; text-align: center;">
                <h4 style="margin: 0; color: #742a2a; font-size: 20px;">
                    🚨 عاجل جداً: مهمتك تنتهي اليوم!
                </h4>
            </div>
            
            <p style="color: #e53e3e; line-height: 1.6; font-size: 18px; font-weight: bold; text-align: center;">
                تنبيه عاجل: لديك مهمة تنتهي اليوم ويجب إنجازها قبل نهاية اليوم.
            </p>
            
            <div style="background: #fff5f5; padding: 25px; border-radius: 8px; margin: 25px 0; border: 3px solid #feb2b2;">
                <h4 style="color: #742a2a; margin-top: 0; display: flex; align-items: center; justify-content: center;">
                    📋 تفاصيل المهمة المستحقة
                </h4>
                <table style="width: 100%; border-collapse: collapse; background: white; border-radius: 5px;">
                    <tr style="background: #fed7d7;">
                        <td style="padding: 12px; color: #742a2a; font-weight: bold; width: 30%; border: 1px solid #feb2b2;">اسم المهمة:</td>
                        <td style="padding: 12px; color: #2d3748; font-weight: bold; border: 1px solid #feb2b2;">{context['task_name']}</td>
                    </tr>
                    <tr>
                        <td style="padding: 12px; color: #742a2a; font-weight: bold; border: 1px solid #feb2b2;">المشروع:</td>
                        <td style="padding: 12px; color: #2d3748; border: 1px solid #feb2b2;">{context['project_name']}</td>
                    </tr>
                    <tr style="background: #fed7d7;">
                        <td style="padding: 12px; color: #742a2a; font-weight: bold; border: 1px solid #feb2b2;">تاريخ الانتهاء:</td>
                        <td style="padding: 12px; color: #e53e3e; font-weight: bold; font-size: 18px; border: 1px solid #feb2b2;">اليوم - {context['due_date']}</td>
                    </tr>
                    <tr>
                        <td style="padding: 12px; color: #742a2a; font-weight: bold; border: 1px solid #feb2b2;">الحالة:</td>
                        <td style="padding: 12px; color: #e53e3e; font-weight: bold; font-size: 16px; border: 1px solid #feb2b2;">مستحقة الآن!</td>
                    </tr>
                    <tr style="background: #fed7d7;">
                        <td style="padding: 12px; color: #742a2a; font-weight: bold; border: 1px solid #feb2b2;">مستوى الإلحاح:</td>
                        <td style="padding: 12px; color: #e53e3e; font-weight: bold; font-size: 16px; border: 1px solid #feb2b2;">{context['urgency_level']}</td>
                    </tr>
                </table>
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{context['task_url']}" style="background: linear-gradient(135deg, #e53e3e 0%, #742a2a 100%); color: white; padding: 20px 40px; text-decoration: none; border-radius: 25px; font-weight: bold; display: inline-block; box-shadow: 0 6px 20px rgba(229, 62, 62, 0.6); font-size: 18px; animation: pulse 1.5s infinite;">
                    🚀 إنجاز المهمة الآن
                </a>
            </div>
            
            <div style="background: #e53e3e; color: white; padding: 20px; border-radius: 8px; margin: 25px 0; text-align: center;">
                <p style="margin: 0; font-weight: bold; font-size: 16px;">
                    ⚠️ هذه المهمة تحتاج إلى اهتمام فوري لتجنب التأخير ⚠️
                </p>
            </div>
            
            <div style="background: #fef5e7; border: 1px solid #d69e2e; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <p style="margin: 0; color: #744210;">
                    📞 <strong>هل تحتاج مساعدة؟</strong> لا تتردد في التواصل مع فريق الدعم أو مشرفك المباشر.
                </p>
            </div>
            
            <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 30px 0;">
            
            <p style="color: #718096; font-size: 14px; text-align: center;">
                مع تحيات فريق {context['site_name']}<br>
                <small>هذا إشعار تلقائي، يرجى عدم الرد على هذا البريد الإلكتروني.</small>
            </p>
        </div>
    </div>
    
    <style>
        @keyframes pulse {{
            0% {{ transform: scale(1); }}
            50% {{ transform: scale(1.05); }}
            100% {{ transform: scale(1); }}
        }}
    </style>
    """
    
    text_content = f"""
مرحباً {context['user_name']}

🚨 عاجل جداً: مهمتك تنتهي اليوم!

تنبيه عاجل: لديك مهمة تنتهي اليوم ويجب إنجازها قبل نهاية اليوم.

تفاصيل المهمة المستحقة:
- اسم المهمة: {context['task_name']}
- المشروع: {context['project_name']}
- تاريخ الانتهاء: اليوم - {context['due_date']}
- الحالة: مستحقة الآن!
- مستوى الإلحاح: {context['urgency_level']}

لعرض المهمة: {context['task_url']}

⚠️ هذه المهمة تحتاج إلى اهتمام فوري لتجنب التأخير ⚠️

📞 هل تحتاج مساعدة؟ لا تتردد في التواصل مع فريق الدعم أو مشرفك المباشر.

مع تحيات فريق {context['site_name']}
---
هذا إشعار تلقائي، يرجى عدم الرد على هذا البريد الإلكتروني.
    """
    
    return subject, html_content, text_content

def create_default_content(context):
    """محتوى افتراضي للتذكيرات"""
    subject = f"تذكير بمهمة - {context['task_name']}"
    
    html_content = f"""
    <div style="font-family: Arial, sans-serif; direction: rtl; text-align: right;">
        <h2>مرحباً {context['user_name']}،</h2>
        <p>هذا تذكير بمهمة لديك:</p>
        <ul>
            <li><strong>اسم المهمة:</strong> {context['task_name']}</li>
            <li><strong>المشروع:</strong> {context['project_name']}</li>
            <li><strong>تاريخ الانتهاء:</strong> {context['due_date']}</li>
        </ul>
        <p><a href="{context['task_url']}">عرض المهمة</a></p>
        <p>مع تحيات فريق {context['site_name']}</p>
    </div>
    """
    
    text_content = f"""
مرحباً {context['user_name']}

هذا تذكير بمهمة لديك:

- اسم المهمة: {context['task_name']}
- المشروع: {context['project_name']}
- تاريخ الانتهاء: {context['due_date']}

لعرض المهمة: {context['task_url']}

مع تحيات فريق {context['site_name']}
    """
    
    return subject, html_content, text_content

def log_deadline_reminder(task, user, reminder_type, status, error_message=None):
    """
    تسجيل إرسال التذكير في قاعدة البيانات
    """
    try:
        from .notification_models import EmailNotificationLog
        
        notification_type_map = {
            'three_days': 'task_due_in_3_days',
            'one_day': 'task_due_tomorrow',
            'same_day': 'task_due_today'
        }
        
        log = EmailNotificationLog.objects.create(
            recipient=user,
            notification_type=notification_type_map.get(reminder_type, 'task_deadline_reminder'),
            subject=f"تذكير مهمة - {task.name}",
            status=status,
            task=task,
            sender=task.created_by,
            error_message=error_message,
            is_reminder=True,
        )
        
        if status == 'sent':
            log.mark_as_sent()
        elif status == 'failed':
            log.mark_as_failed(error_message or 'خطأ غير محدد')
            
    except Exception as e:
        logger.error(f"خطأ في تسجيل التذكير: {str(e)}")

@shared_task
def send_high_priority_reminders():
    """
    إرسال تذكيرات إضافية للمهام عالية الأولوية
    """
    from .models import Task
    from .notification_models import NotificationPreference
    
    today = timezone.now().date()
    
    # المهام عالية الأولوية المستحقة في الأيام القليلة القادمة
    high_priority_tasks = Task.objects.filter(
        priority__in=['high', 'urgent', 'عالية', 'عاجل'],
        status__in=['new', 'in_progress'],
        due_date__lte=today + timedelta(days=2),
        due_date__gte=today
    ).select_related('created_by', 'assigned_to', 'project')
    
    sent_count = 0
    
    for task in high_priority_tasks:
        recipients = get_task_recipients(task)
        
        for recipient in recipients:
            # فحص تفضيلات المستخدم للمهام عالية الأولوية
            preferences = NotificationPreference.get_or_create_for_user(recipient)
            
            if preferences.high_priority_task_reminders and preferences.email_notifications_enabled:
                days_remaining = (task.due_date - today).days
                
                if send_high_priority_reminder(task, recipient, days_remaining):
                    sent_count += 1
    
    logger.info(f"تم إرسال {sent_count} تذكير للمهام عالية الأولوية")
    return sent_count

def send_high_priority_reminder(task, user, days_remaining):
    """
    إرسال تذكير للمهام عالية الأولوية
    """
    try:
        from .services.notification_service import get_notification_service
        
        notification_service = get_notification_service()
        
        # إنشاء محتوى خاص بالمهام عالية الأولوية
        context = create_deadline_context(task, user, days_remaining)
        context['is_high_priority'] = True
        
        subject = f"🔥 عاجل - مهمة عالية الأولوية: {task.name}"
        
        html_content = f"""
        <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; direction: rtl; text-align: right; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #ff4757 0%, #ff3742 100%); color: white; padding: 20px; border-radius: 10px 10px 0 0;">
                <h2 style="margin: 0; font-size: 24px; text-align: center;">🔥 مهمة عالية الأولوية</h2>
            </div>
            
            <div style="background: white; padding: 30px; border-radius: 0 0 10px 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <h3 style="color: #4a5568; margin-top: 0;">مرحباً {context['user_name']}،</h3>
                
                <div style="background: #ffebee; border: 2px solid #ff4757; padding: 20px; margin: 20px 0; border-radius: 8px;">
                    <h4 style="margin: 0; color: #c62828; text-align: center;">
                        🔥 تذكير خاص: مهمة عالية الأولوية تحتاج انتباهك
                    </h4>
                </div>
                
                <p style="color: #4a5568; line-height: 1.6; font-size: 16px;">
                    هذه مهمة مصنفة كعالية الأولوية وتحتاج إلى انتباه خاص. 
                    تبقى <strong style="color: #ff4757;">{days_remaining} يوم</strong> على انتهائها.
                </p>
                
                <div style="background: #fff3e0; padding: 20px; border-radius: 8px; margin: 25px 0; border-left: 4px solid #ff9800;">
                    <h4 style="color: #e65100; margin-top: 0;">📋 تفاصيل المهمة عالية الأولوية</h4>
                    <ul style="list-style: none; padding: 0;">
                        <li style="margin: 10px 0;"><strong>📌 اسم المهمة:</strong> {context['task_name']}</li>
                        <li style="margin: 10px 0;"><strong>🏢 المشروع:</strong> {context['project_name']}</li>
                        <li style="margin: 10px 0;"><strong>⏰ تاريخ الانتهاء:</strong> <span style="color: #ff4757; font-weight: bold;">{context['due_date']}</span></li>
                        <li style="margin: 10px 0;"><strong>🔥 الأولوية:</strong> <span style="color: #ff4757; font-weight: bold;">عالية</span></li>
                    </ul>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{context['task_url']}" style="background: linear-gradient(135deg, #ff4757 0%, #c62828 100%); color: white; padding: 18px 35px; text-decoration: none; border-radius: 25px; font-weight: bold; display: inline-block; box-shadow: 0 4px 15px rgba(255, 71, 87, 0.4); font-size: 16px;">
                        🚀 العمل على المهمة الآن
                    </a>
                </div>
                
                <div style="background: #e8f5e8; border: 1px solid #4caf50; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p style="margin: 0; color: #2e7d32;">
                        💡 <strong>تذكير:</strong> المهام عالية الأولوية لها تأثير كبير على نجاح المشروع.
                    </p>
                </div>
                
                <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 30px 0;">
                
                <p style="color: #718096; font-size: 14px; text-align: center;">
                    مع تحيات فريق {context['site_name']}<br>
                    <small>هذا إشعار تلقائي، يرجى عدم الرد على هذا البريد الإلكتروني.</small>
                </p>
            </div>
        </div>
        """
        
        text_content = f"""
مرحباً {context['user_name']}

🔥 تذكير خاص: مهمة عالية الأولوية تحتاج انتباهك

هذه مهمة مصنفة كعالية الأولوية وتحتاج إلى انتباه خاص.
تبقى {days_remaining} يوم على انتهائها.

تفاصيل المهمة:
- اسم المهمة: {context['task_name']}
- المشروع: {context['project_name']}
- تاريخ الانتهاء: {context['due_date']}
- الأولوية: عالية

لعرض المهمة: {context['task_url']}

💡 تذكير: المهام عالية الأولوية لها تأثير كبير على نجاح المشروع.

مع تحيات فريق {context['site_name']}
---
هذا إشعار تلقائي، يرجى عدم الرد على هذا البريد الإلكتروني.
        """
        
        # إرسال الإيميل
        success = notification_service._send_email(
            recipient=user,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            notification_type='high_priority_reminder',
            task=task
        )
        
        if success:
            log_deadline_reminder(task, user, 'high_priority', 'sent')
            logger.info(f"تم إرسال تذكير أولوية عالية للمستخدم {user.email} للمهمة {task.id}")
            return True
        else:
            log_deadline_reminder(task, user, 'high_priority', 'failed')
            return False
            
    except Exception as e:
        logger.error(f"خطأ في إرسال تذكير الأولوية العالية: {str(e)}")
        log_deadline_reminder(task, user, 'high_priority', 'failed', str(e))
        return False

@shared_task
def cleanup_reminder_trackers():
    """
    تنظيف متتبعات التذكيرات للمهام المكتملة أو المحذوفة
    """
    from .notification_models import TaskReminderTracker
    from .models import Task
    
    try:
        # حذف متتبعات المهام المكتملة
        completed_tasks_trackers = TaskReminderTracker.objects.filter(
            task__status='finished'
        )
        
        deleted_completed = completed_tasks_trackers.delete()
        
        # حذف متتبعات المهام القديمة (أكثر من 30 يوم من انتهائها)
        old_date = timezone.now().date() - timedelta(days=30)
        old_tasks_trackers = TaskReminderTracker.objects.filter(
            task__due_date__lt=old_date
        )
        
        deleted_old = old_tasks_trackers.delete()
        
        # حذف متتبعات المهام غير الموجودة
        orphaned_trackers = TaskReminderTracker.objects.filter(
            task__isnull=True
        )
        
        deleted_orphaned = orphaned_trackers.delete()
        
        total_deleted = deleted_completed[0] + deleted_old[0] + deleted_orphaned[0]
        
        logger.info(f"تم تنظيف {total_deleted} متتبع تذكيرات قديم")
        return total_deleted
        
    except Exception as e:
        logger.error(f"خطأ في تنظيف متتبعات التذكيرات: {str(e)}")
        return 0

@shared_task
def generate_deadline_statistics():
    """
    إنتاج إحصائيات حول تذكيرات المواعيد النهائية
    """
    from .notification_models import EmailNotificationLog, TaskReminderTracker
    from .models import Task
    
    try:
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        
        # إحصائيات التذكيرات المرسلة هذا الأسبوع
        weekly_reminders = EmailNotificationLog.objects.filter(
            notification_type__in=['task_due_in_3_days', 'task_due_tomorrow', 'task_due_today'],
            created_at__date__gte=week_ago,
            status='sent'
        ).count()
        
        # إحصائيات المهام المستحقة
        due_today = Task.objects.filter(
            due_date=today,
            status__in=['new', 'in_progress']
        ).count()
        
        due_tomorrow = Task.objects.filter(
            due_date=today + timedelta(days=1),
            status__in=['new', 'in_progress']
        ).count()
        
        due_in_3_days = Task.objects.filter(
            due_date=today + timedelta(days=3),
            status__in=['new', 'in_progress']
        ).count()
        
        # إحصائيات المهام المتأخرة
        overdue_tasks = Task.objects.filter(
            due_date__lt=today,
            status__in=['new', 'in_progress']
        ).count()
        
        # معدل الاستجابة للتذكيرات
        tasks_with_reminders = TaskReminderTracker.objects.filter(
            last_reminder_date__gte=week_ago
        ).values('task').distinct().count()
        
        completed_after_reminder = Task.objects.filter(
            status='finished',
            updated_at__date__gte=week_ago,
            reminder_trackers__last_reminder_date__gte=week_ago
        ).count()
        
        response_rate = (completed_after_reminder / tasks_with_reminders * 100) if tasks_with_reminders > 0 else 0
        
        stats = {
            'weekly_reminders_sent': weekly_reminders,
            'tasks_due_today': due_today,
            'tasks_due_tomorrow': due_tomorrow,
            'tasks_due_in_3_days': due_in_3_days,
            'overdue_tasks': overdue_tasks,
            'reminder_response_rate': round(response_rate, 2),
            'generated_at': timezone.now().isoformat()
        }
        
        logger.info(f"إحصائيات تذكيرات المواعيد: {stats}")
        return stats
        
    except Exception as e:
        logger.error(f"خطأ في إنتاج الإحصائيات: {str(e)}")
        return {}

# دالة مساعدة لاختبار النظام
@shared_task
def test_deadline_notification_system():
    """
    اختبار نظام تذكيرات المواعيد النهائية
    """
    from .models import Task
    from .services.notification_service import get_notification_service
    
    try:
        # إنشاء مهمة تجريبية للاختبار
        notification_service = get_notification_service()
        
        # البحث عن مهمة تجريبية أو إنشاؤها
        test_task = Task.objects.filter(
            name__icontains='اختبار'
        ).first()
        
        if not test_task:
            logger.warning("لم يتم العثور على مهمة تجريبية للاختبار")
            return False
        
        # اختبار إرسال تذكير
        recipients = get_task_recipients(test_task)
        
        if not recipients:
            logger.warning("لا توجد مستلمون للمهمة التجريبية")
            return False
        
        test_user = recipients[0]
        
        # محاولة إرسال تذكير تجريبي
        success = send_deadline_reminder_to_user(
            test_task, test_user, 'three_days', 3
        )
        
        if success:
            logger.info("تم اختبار نظام التذكيرات بنجاح")
            return True
        else:
            logger.error("فشل في اختبار نظام التذكيرات")
            return False
            
    except Exception as e:
        logger.error(f"خطأ في اختبار النظام: {str(e)}")
        return False