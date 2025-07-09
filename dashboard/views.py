from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime, timedelta
from tasks.models import Task, MonthlyGoal


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
    notifications = []
    
    # Get recent tasks assigned to me (within last 7 days)
    recent_assigned_tasks = Task.objects.filter(
        assigned_to=user,
        created_at__gte=timezone.now() - timedelta(days=7),
        status='new'
    ).select_related('created_by', 'project').order_by('-created_at')[:5]
    
    for task in recent_assigned_tasks:
        notifications.append({
            'type': 'new-task',
            'task_name': task.name,
            'from_user': task.created_by,
            'created_at': task.created_at,
            'task_id': task.pk
        })
    
    # Get recently completed tasks that I assigned to others (within last 3 days)
    completed_assigned_tasks = Task.objects.filter(
        created_by=user,
        assigned_to__isnull=False,
        status='finished',
        updated_at__gte=timezone.now() - timedelta(days=3)
    ).exclude(assigned_to=user).select_related('assigned_to', 'project').order_by('-updated_at')[:5]
    
    for task in completed_assigned_tasks:
        notifications.append({
            'type': 'completed-task',
            'task_name': task.name,
            'from_user': task.assigned_to,  # Who completed it
            'created_at': task.updated_at,
            'task_id': task.pk
        })
    
    # Sort notifications by creation time (newest first)
    notifications = sorted(notifications, key=lambda x: x['created_at'], reverse=True)[:10]
    notifications_count = len(notifications)
    
    # ===== MY TASKS SECTION =====
    # Get user's current tasks (personal tasks + assigned to me + created by me)
    my_tasks = Task.objects.filter(
        Q(created_by=user, assigned_to__isnull=True) |  # My personal tasks
        Q(assigned_to=user) |  # Tasks assigned to me
        Q(created_by=user, assigned_to__isnull=False)  # Tasks I created and assigned to others
    ).filter(status='new').select_related('project', 'created_by', 'assigned_to').order_by('due_date', '-created_at')[:8]
    
    # Add permission flags to each task
    for task in my_tasks:
        task.can_be_edited_by = task.can_be_edited_by(user)
        task.can_be_deleted_by = task.can_be_deleted_by(user)
        task.can_change_status_by = task.can_change_status_by(user)
    
    # ===== STATISTICS =====
    # Total tasks related to user
    total_my_tasks = Task.objects.filter(
        Q(created_by=user) | Q(assigned_to=user)
    ).count()
    
    # Tasks completed today
    completed_tasks_today = Task.objects.filter(
        Q(created_by=user) | Q(assigned_to=user),
        status='finished',
        updated_at__date=today
    ).count()
    
    # Pending tasks (new status)
    pending_tasks = Task.objects.filter(
        Q(created_by=user) | Q(assigned_to=user),
        status='new'
    ).count()
    
    # Overdue tasks
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
        
        # Notifications
        'notifications': notifications,
        'notifications_count': notifications_count,
        
        # Tasks
        'my_tasks': my_tasks,
        
        # Statistics
        'total_my_tasks': total_my_tasks,
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