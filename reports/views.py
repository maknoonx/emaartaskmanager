# Updated Reports Views (reports/views.py)
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from datetime import datetime, date
from calendar import monthrange
import calendar

# Import models from tasks app
try:
    from tasks.models import Task, MonthlyGoal
except ImportError:
    Task = None
    MonthlyGoal = None

Employee = get_user_model()

def report_dashboard_view(request):
    context = {'title': 'التقارير', 'current_page': 'reports'}
    return render(request, 'reports/dashboard.html', context)

def task_reports_view(request):
    context = {'title': 'تقارير المهام', 'current_page': 'reports'}
    return render(request, 'reports/task_reports.html', context)

def employee_reports_view(request):
    context = {'title': 'تقارير الموظفين', 'current_page': 'reports'}
    return render(request, 'reports/employee_reports.html', context)

def program_reports_view(request):
    context = {'title': 'تقارير البرامج', 'current_page': 'reports'}
    return render(request, 'reports/program_reports.html', context)

def financial_reports_view(request):
    context = {'title': 'التقارير المالية', 'current_page': 'reports'}
    return render(request, 'reports/financial_reports.html', context)
# Updated Reports Views (reports/views.py)
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from datetime import datetime, date
from calendar import monthrange
import calendar

# Import models from tasks app
try:
    from tasks.models import Task, MonthlyGoal
except ImportError:
    Task = None
    MonthlyGoal = None

Employee = get_user_model()

def report_dashboard_view(request):
    context = {'title': 'التقارير', 'current_page': 'reports'}
    return render(request, 'reports/dashboard.html', context)

def task_reports_view(request):
    context = {'title': 'تقارير المهام', 'current_page': 'reports'}
    return render(request, 'reports/task_reports.html', context)

def employee_reports_view(request):
    context = {'title': 'تقارير الموظفين', 'current_page': 'reports'}
    return render(request, 'reports/employee_reports.html', context)

def program_reports_view(request):
    context = {'title': 'تقارير البرامج', 'current_page': 'reports'}
    return render(request, 'reports/program_reports.html', context)

def financial_reports_view(request):
    context = {'title': 'التقارير المالية', 'current_page': 'reports'}
    return render(request, 'reports/financial_reports.html', context)




# ===== تحديث Monthly Report View =====
@login_required
def monthly_report_view(request):
    """
    Monthly Task Report - Shows comprehensive report including ALL tasks
    """
    # الحصول على معايير الفلتر
    selected_month = request.GET.get('month', str(datetime.now().month))
    selected_year = request.GET.get('year', str(datetime.now().year))
    
    try:
        month = int(selected_month)
        year = int(selected_year)
    except (ValueError, TypeError):
        month = datetime.now().month
        year = datetime.now().year
    
    # أسماء الشهور بالعربية
    month_names = {
        1: 'يناير', 2: 'فبراير', 3: 'مارس', 4: 'أبريل',
        5: 'مايو', 6: 'يونيو', 7: 'يوليو', 8: 'أغسطس',
        9: 'سبتمبر', 10: 'أكتوبر', 11: 'نوفمبر', 12: 'ديسمبر'
    }
    
    month_name = month_names.get(month, 'غير محدد')
    
    # نطاق التاريخ للشهر
    first_day = date(year, month, 1)
    last_day = date(year, month, monthrange(year, month)[1])
    
    # الحصول على بيانات المستخدم الحالي فقط
    employee = request.user
    
    # تحضير بيانات التقرير
    if Task:  # التأكد من توفر نموذج Task
        # جميع المهام المرتبطة بالموظف في الشهر المحدد (مُنشأة أو مُسندة)
        all_related_tasks = Task.objects.filter(
            Q(created_by=employee) | Q(assigned_to=employee),
            created_at__date__gte=first_day,
            created_at__date__lte=last_day
        ).distinct().order_by('created_at')
        
        # المهام التي أنشأها الموظف في الشهر (شامل المُسندة للآخرين)
        tasks_created = Task.objects.filter(
            created_by=employee,
            created_at__date__gte=first_day,
            created_at__date__lte=last_day
        ).distinct().order_by('created_at')
        
        # المهام المُسندة للموظف في الشهر
        tasks_assigned_to_me = Task.objects.filter(
            assigned_to=employee,
            created_at__date__gte=first_day,
            created_at__date__lte=last_day
        ).distinct().order_by('created_at')
        
        # المهام المكتملة في الشهر المحدد
        tasks_completed = Task.objects.filter(
            Q(created_by=employee) | Q(assigned_to=employee),
            status='finished',
            updated_at__date__gte=first_day,
            updated_at__date__lte=last_day
        ).distinct().order_by('updated_at')
        
        # المهام المتأخرة
        overdue_tasks = Task.objects.filter(
            Q(created_by=employee) | Q(assigned_to=employee),
            due_date__gte=first_day,
            due_date__lte=last_day,
            status='new'
        ).distinct().order_by('due_date')
        
        # المهام المُسندة للآخرين من قبل الموظف
        tasks_assigned_to_others = Task.objects.filter(
            created_by=employee,
            assigned_to__isnull=False,
            created_at__date__gte=first_day,
            created_at__date__lte=last_day
        ).exclude(assigned_to=employee).distinct().order_by('created_at')
        
    else:
        # في حالة عدم توفر نموذج Task
        all_related_tasks = []
        tasks_created = []
        tasks_assigned_to_me = []
        tasks_completed = []
        overdue_tasks = []
        tasks_assigned_to_others = []
    
    # الحصول على الأهداف الشهرية
    monthly_goals = []
    if MonthlyGoal:
        monthly_goals = MonthlyGoal.objects.filter(
            employee=employee,
            month=month,
            year=year
        )
    
    # حساب الإحصائيات الشاملة
    total_all_related = len(all_related_tasks)
    total_created = len(tasks_created)
    total_assigned_to_me = len(tasks_assigned_to_me)
    total_completed = len(tasks_completed)
    total_overdue = len(overdue_tasks)
    total_assigned_to_others = len(tasks_assigned_to_others)
    
    completion_rate = (total_completed / total_all_related * 100) if total_all_related > 0 else 0
    
    # إنشاء بيانات تقرير الموظف
    employee_report = {
        'employee': employee,
        'all_related_tasks': all_related_tasks,
        'tasks_created': tasks_created,
        'tasks_assigned_to_me': tasks_assigned_to_me,
        'tasks_completed': tasks_completed,
        'overdue_tasks': overdue_tasks,
        'tasks_assigned_to_others': tasks_assigned_to_others,
        'monthly_goals': monthly_goals,
        'stats': {
            'total_all_related': total_all_related,
            'total_created': total_created,
            'total_assigned_to_me': total_assigned_to_me,
            'total_completed': total_completed,
            'total_overdue': total_overdue,
            'total_assigned_to_others': total_assigned_to_others,
            'completion_rate': round(completion_rate, 1),
        }
    }
    
    # نطاق السنوات للفلتر
    current_year = datetime.now().year
    year_range = list(range(current_year - 2, current_year + 3))
    
    context = {
        'title': f'تقريري الشهري - {month_name} {year}',
        'current_page': 'reports',
        'employee_report': employee_report,
        'selected_month': month,
        'selected_year': year,
        'month_name': month_name,
        'month_range': range(1, 13),
        'year_range': year_range,
        'month_names': month_names,
        'report_date': f"{month_name} {year}",
        'has_data': total_all_related > 0 or len(monthly_goals) > 0,
    }
    
    return render(request, 'reports/my_monthly_report.html', context)



@login_required
def monthly_report_print_view(request):
    """
    Printable version of monthly report for the current logged-in user
    """
    selected_month = request.GET.get('month', str(datetime.now().month))
    selected_year = request.GET.get('year', str(datetime.now().year))
    
    # Use current logged-in user
    employee = request.user
    
    try:
        month = int(selected_month)
        year = int(selected_year)
    except (ValueError, TypeError):
        month = datetime.now().month
        year = datetime.now().year
    
    # Get month name in Arabic
    month_names = {
        1: 'يناير', 2: 'فبراير', 3: 'مارس', 4: 'أبريل',
        5: 'مايو', 6: 'يونيو', 7: 'يوليو', 8: 'أغسطس',
        9: 'سبتمبر', 10: 'أكتوبر', 11: 'نوفمبر', 12: 'ديسمبر'
    }
    
    month_name = month_names.get(month, 'غير محدد')
    
    # Get date range for the month
    first_day = date(year, month, 1)
    last_day = date(year, month, monthrange(year, month)[1])
    
    # Get tasks data
    if Task:  # Check if Task model is available
        # Tasks created in the selected month
        tasks_created = Task.objects.filter(
            Q(created_by=employee) | Q(assigned_to=employee),
            created_at__date__gte=first_day,
            created_at__date__lte=last_day
        ).distinct().order_by('created_at')
        
        # Tasks completed in the selected month
        tasks_completed = Task.objects.filter(
            Q(created_by=employee) | Q(assigned_to=employee),
            status='finished',
            updated_at__date__gte=first_day,
            updated_at__date__lte=last_day
        ).distinct().order_by('updated_at')
        
        # Tasks that were due in the month but not completed
        overdue_tasks = Task.objects.filter(
            Q(created_by=employee) | Q(assigned_to=employee),
            due_date__gte=first_day,
            due_date__lte=last_day,
            status='new'
        ).distinct().order_by('due_date')
        
    else:
        tasks_created = []
        tasks_completed = []
        overdue_tasks = []
    
    # Get monthly goals
    monthly_goals = []
    if MonthlyGoal:
        monthly_goals = MonthlyGoal.objects.filter(
            employee=employee,
            month=month,
            year=year
        )
    
    # Calculate statistics
    total_created = len(tasks_created)
    total_completed = len(tasks_completed)
    total_overdue = len(overdue_tasks)
    completion_rate = (total_completed / total_created * 100) if total_created > 0 else 0
    
    context = {
        'employee': employee,
        'month_name': month_name,
        'year': year,
        'report_date': f"{month_name} {year}",
        'tasks_created': tasks_created,
        'tasks_completed': tasks_completed,
        'overdue_tasks': overdue_tasks,
        'monthly_goals': monthly_goals,
        'stats': {
            'total_created': total_created,
            'total_completed': total_completed,
            'total_overdue': total_overdue,
            'completion_rate': round(completion_rate, 1),
        },
        'print_date': datetime.now().strftime('%d/%m/%Y'),
    }
    
    return render(request, 'reports/monthly_report_print.html', context)

def yearly_report_view(request):
    context = {'title': 'التقرير السنوي', 'current_page': 'reports'}
    return render(request, 'reports/yearly_report.html', context)

def custom_report_view(request):
    context = {'title': 'تقرير مخصص', 'current_page': 'reports'}
    return render(request, 'reports/custom_report.html', context)

def export_report_view(request, report_type):
    # Handle report export logic (PDF, Excel, etc.)
    from django.http import HttpResponse
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="report_{report_type}.pdf"'
    return response

def generate_report_view(request):
    # Handle dynamic report generation
    context = {'title': 'إنشاء تقرير', 'current_page': 'reports'}
    return render(request, 'reports/generate_report.html', context)