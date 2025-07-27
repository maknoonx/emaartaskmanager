from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime, timedelta
from tasks.models import Task, MonthlyGoal


# ===== تحديث Dashboard View =====
@login_required
def dashboard_view(request):
    """Main dashboard view with notifications and task management"""
    user = request.user
    today = timezone.now().date()
    
    # Get greeting message based on time
    current_hour = datetime.now().hour
    if current_hour < 12:
        greeting_message = "صباح الخير! نتمنى لك يوماً مثمراً ومليئاً بالإنجازات"
    elif current_hour < 17:
        greeting_message = "مساء الخير! استمر في العمل الرائع"
    else:
        greeting_message = "مساء الخير! وقت لمراجعة إنجازات اليوم"
    
    # ===== NOTIFICATIONS SECTION =====
    # (الإشعارات تبقى كما هي...)
    
    # ===== MY TASKS SECTION =====
    # Get user's current tasks (ALL tasks related to user - created OR assigned)
    my_tasks = Task.objects.filter(
        Q(created_by=user) | Q(assigned_to=user)
    ).filter(status='new').select_related('project', 'created_by', 'assigned_to').order_by('due_date', '-created_at')[:8]
    
    # Add permission flags to each task
    for task in my_tasks:
        task.can_be_edited_by = task.can_be_edited_by(user)
        task.can_be_deleted_by = task.can_be_deleted_by(user)
        task.can_change_status_by = task.can_change_status_by(user)
    
    # ===== إحصائيات محدّثة =====
    # إجمالي جميع المهام (المُنشأة أو المُسندة للمستخدم)
    total_my_tasks = Task.objects.filter(
        Q(created_by=user) | Q(assigned_to=user)
    ).count()
    
    # المهام المُنشأة من قبل المستخدم (شامل المُسندة للآخرين)
    my_created_tasks = Task.objects.filter(created_by=user).count()
    
    # المهام المُسندة للمستخدم فقط
    assigned_to_me_tasks = Task.objects.filter(assigned_to=user).count()
    
    # المهام المُنشأة والمُسندة للآخرين
    my_assigned_to_others = Task.objects.filter(
        created_by=user, 
        assigned_to__isnull=False
    ).exclude(assigned_to=user).count()
    
    # المهام المكتملة اليوم (جميع المهام المرتبطة بالمستخدم)
    completed_tasks_today = Task.objects.filter(
        Q(created_by=user) | Q(assigned_to=user),
        status='finished',
        updated_at__date=today
    ).count()
    
    # المهام المعلقة (حالة جديد)
    pending_tasks = Task.objects.filter(
        Q(created_by=user) | Q(assigned_to=user),
        status='new'
    ).count()
    
    # المهام المتأخرة
    overdue_tasks = Task.objects.filter(
        Q(created_by=user) | Q(assigned_to=user),
        status='new',
        due_date__lt=today
    ).count()
    
    # Monthly goals count for current user
    monthly_goals_count = MonthlyGoal.objects.filter(
        employee=user,
        year=datetime.now().year
    ).count()
    
    context = {
        'title': 'الرئيسية',
        'current_page': 'dashboard',
        'greeting_message': greeting_message,
        
        # Tasks
        'my_tasks': my_tasks,
        
        # إحصائيات مفصّلة
        'total_my_tasks': total_my_tasks,
        'my_created_tasks': my_created_tasks,
        'assigned_to_me_tasks': assigned_to_me_tasks,
        'my_assigned_to_others': my_assigned_to_others,
        'completed_tasks_today': completed_tasks_today,
        'pending_tasks': pending_tasks,
        'overdue_tasks': overdue_tasks,
        'monthly_goals_count': monthly_goals_count,
    }
    
    return render(request, 'dashboard/dashboard.html', context)



@login_required
def profile_view(request):
    """User profile view with personal information and preferences"""
    user = request.user
    
    # Get user's task statistics
    task_stats = {
        'total_created': Task.objects.filter(created_by=user).count(),
        'total_assigned': Task.objects.filter(assigned_to=user).count(),
        'completed_this_month': Task.objects.filter(
            Q(created_by=user) | Q(assigned_to=user),
            status='finished',
            updated_at__month=datetime.now().month,
            updated_at__year=datetime.now().year
        ).count(),
        'overdue': Task.objects.filter(
            Q(created_by=user) | Q(assigned_to=user),
            status='new',
            due_date__lt=timezone.now().date()
        ).count()
    }
    
    # Get monthly goals count
    monthly_goals = MonthlyGoal.objects.filter(employee=user).count()
    
    context = {
        'title': 'الملف الشخصي',
        'current_page': 'profile',
        'task_stats': task_stats,
        'monthly_goals': monthly_goals,
    }
    
    return render(request, 'dashboard/profile.html', context)


@login_required
def settings_view(request):
    """System settings and preferences view"""
    context = {
        'title': 'الإعدادات',
        'current_page': 'settings',
    }
    
    return render(request, 'dashboard/settings.html', context)


@login_required
def get_notifications_ajax(request):
    """AJAX endpoint to get fresh notifications without page reload"""
    from django.http import JsonResponse
    
    user = request.user
    
    # Get recent notifications (similar logic as in dashboard_view)
    notifications = []
    
    # Recent tasks assigned to me
    recent_assigned_tasks = Task.objects.filter(
        assigned_to=user,
        created_at__gte=timezone.now() - timedelta(days=7),
        status='new'
    ).select_related('created_by').order_by('-created_at')[:5]
    
    for task in recent_assigned_tasks:
        notifications.append({
            'type': 'new-task',
            'task_name': task.name,
            'from_user_name': task.created_by.name,
            'from_user_avatar': task.created_by.profile_picture.url if task.created_by.profile_picture else None,
            'created_at': task.created_at.strftime('%Y-%m-%d %H:%M'),
            'task_id': task.pk
        })
    
    # Recently completed tasks I assigned
    completed_assigned_tasks = Task.objects.filter(
        created_by=user,
        assigned_to__isnull=False,
        status='finished',
        updated_at__gte=timezone.now() - timedelta(days=3)
    ).exclude(assigned_to=user).select_related('assigned_to').order_by('-updated_at')[:5]
    
    for task in completed_assigned_tasks:
        notifications.append({
            'type': 'completed-task',
            'task_name': task.name,
            'from_user_name': task.assigned_to.name,
            'from_user_avatar': task.assigned_to.profile_picture.url if task.assigned_to.profile_picture else None,
            'created_at': task.updated_at.strftime('%Y-%m-%d %H:%M'),
            'task_id': task.pk
        })
    
    # Sort by creation time
    notifications = sorted(notifications, key=lambda x: x['created_at'], reverse=True)[:10]
    
    return JsonResponse({
        'notifications': notifications,
        'count': len(notifications)
    })