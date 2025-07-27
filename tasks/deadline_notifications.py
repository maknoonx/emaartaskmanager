# tasks/deadline_notifications.py
# نظام إشعارات التذكير بمواعيد انتهاء المهام

from celery import shared_task
from django.utils import timezone
from datetime import timedelta, date
from django.contrib.auth import get_user_model
import logging

Employee = get_user_model()
logger = logging.getLogger('notifications')

@shared_task
def send_task_deadline_reminders():
    """
    إرسال تذكيرات للمهام قريبة الانتهاء
    يتم تشغيلها يومياً للتحقق من المهام التي تحتاج تذكير
    """
    from .models import Task
    from .services.notification_service import get_notification_service
    
    notification_service = get_notification_service()
    today = timezone.now().date()
    
    # المهام التي تنتهي بعد 3 أيام
    three_days_later = today + timedelta(days=3)
    tasks_3_days = Task.objects.filter(
        due_date=three_days_later,
        status__in=['new', 'in_progress']
    ).select_related('created_by', 'assigned_to', 'project')
    
    # المهام التي تنتهي غداً (بعد يوم واحد)
    tomorrow = today + timedelta(days=1)
    tasks_1_day = Task.objects.filter(
        due_date=tomorrow,
        status__in=['new', 'in_progress']
    ).select_related('created_by', 'assigned_to', 'project')
    
    # المهام التي انتهت اليوم
    tasks_due_today = Task.objects.filter(
        due_date=today,
        status__in=['new', 'in_progress']
    ).select_related('created_by', 'assigned_to', 'project')
    
    total_sent = 0
    
    # إرسال تذكير للمهام التي تنتهي بعد 3 أيام
    for task in tasks_3_days:
        if send_deadline_reminder(task, days_remaining=3):
            total_sent += 1
    
    # إرسال تذكير للمهام التي تنتهي غداً
    for task in tasks_1_day:
        if send_deadline_reminder(task, days_remaining=1):
            total_sent += 1
    
    # إرسال تذكير للمهام المستحقة اليوم
    for task in tasks_due_today:
        if send_deadline_reminder(task, days_remaining=0):
            total_sent += 1
    
    logger.info(f"تم إرسال {total_sent} تذكير لمواعيد انتهاء المهام")
    return total_sent

def send_deadline_reminder(task, days_remaining):
    """
    إرسال تذكير لمهمة محددة قريبة من الانتهاء
    """
    from .services.notification_service import get_notification_service
    
    notification_service = get_notification_service()
    
    # قائمة المستلمين (منشئ المهمة + المُسند إليه)
    recipients = set()
    
    if task.created_by:
        recipients.add(task.created_by)
    
    if task.assigned_to and task.assigned_to != task.created_by:
        recipients.add(task.assigned_to)
    
    sent_count = 0
    
    for recipient in recipients:
        try:
            # التحقق من تفضيلات الإشعارات
            from .notification_models import NotificationPreference
            preferences = NotificationPreference.get_or_create_for_user(recipient)
            
            if not preferences.email_notifications_enabled or not preferences.task_deadline_reminders:
                continue
            
            # تحديد نوع التذكير
            if days_remaining == 3:
                reminder_type = 'task_due_in_3_days'
                subject_prefix = 'تذكير: تنتهي مهمتك بعد 3 أيام'
            elif days_remaining == 1:
                reminder_type = 'task_due_tomorrow'
                subject_prefix = 'تذكير: تنتهي مهمتك غداً'
            else:  # days_remaining == 0
                reminder_type = 'task_due_today'
                subject_prefix = 'تنبيه عاجل: مهمتك تنتهي اليوم'
            
            # إعداد السياق
            context = {
                'task': task,
                'recipient': recipient,
                'days_remaining': days_remaining,
                'task_name': task.name,
                'project_name': task.project.name if task.project else 'غير محدد',
                'due_date': task.due_date.strftime('%Y-%m-%d'),
                'user_name': recipient.name,
                'creator_name': task.created_by.name if task.created_by else '',
                'assignee_name': task.assigned_to.name if task.assigned_to else '',
                'task_url': f"{notification_service.site_url}/tasks/{task.pk}/",
                'site_name': notification_service.site_name,
                'site_url': notification_service.site_url,
            }
            
            # إنشاء المحتوى
            subject = f"{subject_prefix} - {task.name}"
            
            if days_remaining == 3:
                html_content = render_3_days_reminder_html(context)
                text_content = render_3_days_reminder_text(context)
            elif days_remaining == 1:
                html_content = render_1_day_reminder_html(context)
                text_content = render_1_day_reminder_text(context)
            else:
                html_content = render_due_today_html(context)
                text_content = render_due_today_text(context)
            
            # إرسال الإيميل
            success = notification_service._send_email(
                recipient=recipient,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                notification_type=reminder_type,
                task=task
            )
            
            if success:
                sent_count += 1
                logger.info(f"تم إرسال تذكير {reminder_type} للمستخدم {recipient.email} للمهمة {task.id}")
            
        except Exception as e:
            logger.error(f"فشل إرسال تذكير للمستخدم {recipient.email} للمهمة {task.id}: {str(e)}")
    
    return sent_count > 0

def render_3_days_reminder_html(context):
    """قالب HTML للتذكير بـ 3 أيام"""
    return f"""
    <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; direction: rtl; text-align: right;">
        <h2 style="color: #0066cc;">مرحباً {context['user_name']}،</h2>
        
        <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <h3 style="color: #856404; margin: 0;">
                📅 تذكير: تنتهي مهمتك بعد 3 أيام
            </h3>
        </div>
        
        <p>نود تذكيرك بأن لديك مهمة ستنتهي بعد 3 أيام من اليوم.</p>
        
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <h3 style="color: #495057;">📋 تفاصيل المهمة:</h3>
            <ul style="list-style-type: none; padding: 0;">
                <li style="margin: 8px 0;"><strong>اسم المهمة:</strong> {context['task_name']}</li>
                <li style="margin: 8px 0;"><strong>المشروع:</strong> {context['project_name']}</li>
                <li style="margin: 8px 0;"><strong>تاريخ الانتهاء:</strong> <span style="color: #fd7e14; font-weight: bold;">{context['due_date']}</span></li>
                <li style="margin: 8px 0;"><strong>المتبقي:</strong> <span style="color: #fd7e14; font-weight: bold;">3 أيام</span></li>
            </ul>
        </div>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="{context['task_url']}" style="background-color: #0066cc; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                عرض المهمة والعمل عليها
            </a>
        </div>
        
        <p style="color: #6c757d;">يرجى التخطيط لإنجاز هذه المهمة في الوقت المحدد لتجنب التأخير.</p>
        
        <hr style="border: 1px solid #dee2e6; margin: 30px 0;">
        <p style="color: #6c757d; font-size: 12px;">
            مع تحيات فريق {context['site_name']}<br>
            هذا إشعار تلقائي، يرجى عدم الرد على هذا البريد الإلكتروني.
        </p>
    </div>
    """

def render_1_day_reminder_html(context):
    """قالب HTML للتذكير بيوم واحد"""
    return f"""
    <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; direction: rtl; text-align: right;">
        <h2 style="color: #0066cc;">مرحباً {context['user_name']}،</h2>
        
        <div style="background-color: #f8d7da; border: 1px solid #f5c6cb; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <h3 style="color: #721c24; margin: 0;">
                ⏰ تنبيه مهم: تنتهي مهمتك غداً!
            </h3>
        </div>
        
        <p><strong>هذا تذكير عاجل</strong> بأن لديك مهمة ستنتهي غداً (خلال 24 ساعة).</p>
        
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <h3 style="color: #495057;">📋 تفاصيل المهمة:</h3>
            <ul style="list-style-type: none; padding: 0;">
                <li style="margin: 8px 0;"><strong>اسم المهمة:</strong> {context['task_name']}</li>
                <li style="margin: 8px 0;"><strong>المشروع:</strong> {context['project_name']}</li>
                <li style="margin: 8px 0;"><strong>تاريخ الانتهاء:</strong> <span style="color: #dc3545; font-weight: bold;">{context['due_date']}</span></li>
                <li style="margin: 8px 0;"><strong>المتبقي:</strong> <span style="color: #dc3545; font-weight: bold;">يوم واحد فقط!</span></li>
            </ul>
        </div>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="{context['task_url']}" style="background-color: #dc3545; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 16px;">
                عرض المهمة فوراً
            </a>
        </div>
        
        <p style="color: #dc3545; font-weight: bold;">⚠️ يرجى إنجاز هذه المهمة اليوم لتجنب التأخير!</p>
        
        <hr style="border: 1px solid #dee2e6; margin: 30px 0;">
        <p style="color: #6c757d; font-size: 12px;">
            مع تحيات فريق {context['site_name']}<br>
            هذا إشعار تلقائي، يرجى عدم الرد على هذا البريد الإلكتروني.
        </p>
    </div>
    """

def render_due_today_html(context):
    """قالب HTML للمهام المستحقة اليوم"""
    return f"""
    <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; direction: rtl; text-align: right;">
        <h2 style="color: #0066cc;">مرحباً {context['user_name']}،</h2>
        
        <div style="background-color: #f8d7da; border: 2px solid #dc3545; padding: 20px; border-radius: 5px; margin: 20px 0;">
            <h3 style="color: #721c24; margin: 0; font-size: 18px;">
                🚨 عاجل جداً: مهمتك تنتهي اليوم!
            </h3>
        </div>
        
        <p style="color: #dc3545; font-weight: bold; font-size: 16px;">
            تنبيه عاجل: لديك مهمة تنتهي اليوم ويجب إنجازها قبل نهاية اليوم.
        </p>
        
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <h3 style="color: #495057;">📋 تفاصيل المهمة:</h3>
            <ul style="list-style-type: none; padding: 0;">
                <li style="margin: 8px 0;"><strong>اسم المهمة:</strong> {context['task_name']}</li>
                <li style="margin: 8px 0;"><strong>المشروع:</strong> {context['project_name']}</li>
                <li style="margin: 8px 0;"><strong>تاريخ الانتهاء:</strong> <span style="color: #dc3545; font-weight: bold;">اليوم - {context['due_date']}</span></li>
                <li style="margin: 8px 0;"><strong>الحالة:</strong> <span style="color: #dc3545; font-weight: bold;">مستحقة الآن!</span></li>
            </ul>
        </div>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="{context['task_url']}" style="background-color: #dc3545; color: white; padding: 20px 40px; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 18px; animation: blink 1s linear infinite;">
                إنجاز المهمة الآن
            </a>
        </div>
        
        <div style="background-color: #dc3545; color: white; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <p style="margin: 0; font-weight: bold; text-align: center;">
                ⚠️ هذه المهمة تحتاج إلى اهتمام فوري لتجنب التأخير ⚠️
            </p>
        </div>
        
        <hr style="border: 1px solid #dee2e6; margin: 30px 0;">
        <p style="color: #6c757d; font-size: 12px;">
            مع تحيات فريق {context['site_name']}<br>
            هذا إشعار تلقائي، يرجى عدم الرد على هذا البريد الإلكتروني.
        </p>
    </div>
    """

def render_3_days_reminder_text(context):
    """قالب نصي للتذكير بـ 3 أيام"""
    return f"""
مرحباً {context['user_name']}

📅 تذكير: تنتهي مهمتك بعد 3 أيام

نود تذكيرك بأن لديك مهمة ستنتهي بعد 3 أيام من اليوم.

تفاصيل المهمة:
- اسم المهمة: {context['task_name']}
- المشروع: {context['project_name']}
- تاريخ الانتهاء: {context['due_date']}
- المتبقي: 3 أيام

لعرض المهمة: {context['task_url']}

يرجى التخطيط لإنجاز هذه المهمة في الوقت المحدد لتجنب التأخير.

مع تحيات فريق {context['site_name']}
---
هذا إشعار تلقائي، يرجى عدم الرد على هذا البريد الإلكتروني.
    """

def render_1_day_reminder_text(context):
    """قالب نصي للتذكير بيوم واحد"""
    return f"""
مرحباً {context['user_name']}

⏰ تنبيه مهم: تنتهي مهمتك غداً!

هذا تذكير عاجل بأن لديك مهمة ستنتهي غداً (خلال 24 ساعة).

تفاصيل المهمة:
- اسم المهمة: {context['task_name']}
- المشروع: {context['project_name']}
- تاريخ الانتهاء: {context['due_date']}
- المتبقي: يوم واحد فقط!

لعرض المهمة: {context['task_url']}

⚠️ يرجى إنجاز هذه المهمة اليوم لتجنب التأخير!

مع تحيات فريق {context['site_name']}
---
هذا إشعار تلقائي، يرجى عدم الرد على هذا البريد الإلكتروني.
    """

def render_due_today_text(context):
    """قالب نصي للمهام المستحقة اليوم"""
    return f"""
مرحباً {context['user_name']}

🚨 عاجل جداً: مهمتك تنتهي اليوم!

تنبيه عاجل: لديك مهمة تنتهي اليوم ويجب إنجازها قبل نهاية اليوم.

تفاصيل المهمة:
- اسم المهمة: {context['task_name']}
- المشروع: {context['project_name']}
- تاريخ الانتهاء: اليوم - {context['due_date']}
- الحالة: مستحقة الآن!

لعرض المهمة: {context['task_url']}

⚠️ هذه المهمة تحتاج إلى اهتمام فوري لتجنب التأخير ⚠️

مع تحيات فريق {context['site_name']}
---
هذا إشعار تلقائي، يرجى عدم الرد على هذا البريد الإلكتروني.
    """