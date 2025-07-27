from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
import json

Employee = get_user_model()

@login_required
def index(request):
    """
    Display all employees with search and filter functionality including task statistics
    """
    # Import Task model
    try:
        from tasks.models import Task
        has_tasks = True
    except ImportError:
        has_tasks = False
    
    employees = Employee.objects.all()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        employees = employees.filter(
            Q(name__icontains=search_query) |
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(job_title__icontains=search_query) |
            Q(job_number__icontains=search_query)
        )
    
    # Filter by section
    section_filter = request.GET.get('section', '')
    if section_filter:
        employees = employees.filter(section=section_filter)
    
    # Filter by active status
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        employees = employees.filter(is_active_employee=True)
    elif status_filter == 'inactive':
        employees = employees.filter(is_active_employee=False)
    
    # Add task statistics to each employee
    employees_with_stats = []
    for employee in employees:
        if has_tasks:
            # Calculate comprehensive task statistics for each employee
            total_tasks = Task.objects.filter(
                Q(created_by=employee) | Q(assigned_to=employee)
            ).count()
            
            created_tasks = Task.objects.filter(created_by=employee).count()
            assigned_tasks = Task.objects.filter(assigned_to=employee).count()
            
            # Tasks assigned to others by this employee
            assigned_to_others = Task.objects.filter(
                created_by=employee,
                assigned_to__isnull=False
            ).exclude(assigned_to=employee).count()
            
            completed_tasks = Task.objects.filter(
                Q(created_by=employee) | Q(assigned_to=employee),
                status='finished'
            ).count()
            
            pending_tasks = Task.objects.filter(
                Q(created_by=employee) | Q(assigned_to=employee),
                status='new'
            ).count()
            
            # Calculate completion rate
            completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            
            # Add stats to employee object
            employee.task_stats = {
                'total_tasks': total_tasks,
                'created_tasks': created_tasks,
                'assigned_tasks': assigned_tasks,
                'assigned_to_others': assigned_to_others,
                'completed_tasks': completed_tasks,
                'pending_tasks': pending_tasks,
                'completion_rate': round(completion_rate, 1)
            }
        else:
            # If no Task model, set empty stats
            employee.task_stats = {
                'total_tasks': 0,
                'created_tasks': 0,
                'assigned_tasks': 0,
                'assigned_to_others': 0,
                'completed_tasks': 0,
                'pending_tasks': 0,
                'completion_rate': 0
            }
        
        employees_with_stats.append(employee)
    
    # Pagination
    paginator = Paginator(employees_with_stats, 10)  # 10 employees per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get section choices for filter dropdown
    section_choices = Employee.SECTION_CHOICES
    
    # Calculate overall statistics
    if has_tasks:
        total_all_tasks = Task.objects.count()
        total_completed_tasks = Task.objects.filter(status='finished').count()
        total_pending_tasks = Task.objects.filter(status='new').count()
        
        # Tasks assigned to others statistics
        total_assigned_to_others = Task.objects.filter(
            assigned_to__isnull=False
        ).exclude(created_by=None).count()
        
        overall_completion_rate = (total_completed_tasks / total_all_tasks * 100) if total_all_tasks > 0 else 0
    else:
        total_all_tasks = 0
        total_completed_tasks = 0
        total_pending_tasks = 0
        total_assigned_to_others = 0
        overall_completion_rate = 0
    
    context = {
        'title': 'إدارة الموظفين',
        'current_page': 'employees',
        'page_obj': page_obj,
        'search_query': search_query,
        'section_filter': section_filter,
        'status_filter': status_filter,
        'section_choices': section_choices,
        
        # Employee statistics
        'total_employees': Employee.objects.count(),
        'active_employees': Employee.objects.filter(is_active_employee=True).count(),
        'inactive_employees': Employee.objects.filter(is_active_employee=False).count(),
        
        # Task statistics
        'has_tasks': has_tasks,
        'total_all_tasks': total_all_tasks,
        'total_completed_tasks': total_completed_tasks,
        'total_pending_tasks': total_pending_tasks,
        'total_assigned_to_others': total_assigned_to_others,
        'overall_completion_rate': round(overall_completion_rate, 1),
    }
    
    return render(request, 'employees/index.html', context)



@login_required
def detail(request, pk):
    """
    Display employee detail in modal or separate page
    """
    employee = get_object_or_404(Employee, pk=pk)
    
    # Check if request is AJAX for modal display
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        context = {
            'employee': employee,
            'can_delete': employee.can_be_deleted(),
            'deletion_blockers': employee.get_deletion_blockers() if not employee.can_be_deleted() else []
        }
        return render(request, 'employees/partials/employee_detail_modal.html', context)
    
    context = {
        'title': f'تفاصيل الموظف - {employee.display_name}',
        'current_page': 'employees',
        'employee': employee,
        'can_delete': employee.can_be_deleted(),
        'deletion_blockers': employee.get_deletion_blockers() if not employee.can_be_deleted() else []
    }
    
    return render(request, 'employees/detail.html', context)

@login_required
@require_http_methods(["GET", "POST"])
def create(request):
    """
    Create new employee
    """
    if request.method == 'POST':
        try:
            # Extract data from POST request
            data = {
                'username': request.POST.get('username'),
                'name': request.POST.get('name'),
                'email': request.POST.get('email'),
                'job_title': request.POST.get('job_title'),
                'job_number': request.POST.get('job_number'),
                'mobile_number': request.POST.get('mobile_number'),
                'section': request.POST.get('section'),
                'notes': request.POST.get('notes', ''),
                'is_active_employee': request.POST.get('is_active_employee') == 'on'
            }
            
            # Validate required fields
            required_fields = ['username', 'name', 'email', 'job_title', 'job_number', 'mobile_number', 'section']
            for field in required_fields:
                if not data.get(field):
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False, 
                            'error': f'الحقل {field} مطلوب'
                        })
                    messages.error(request, f'الحقل {field} مطلوب')
                    return redirect('employees:index')
            
            # Check for unique constraints
            if Employee.objects.filter(username=data['username']).exists():
                error_msg = 'اسم المستخدم موجود مسبقاً'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': error_msg})
                messages.error(request, error_msg)
                return redirect('employees:index')
            
            if Employee.objects.filter(email=data['email']).exists():
                error_msg = 'البريد الإلكتروني موجود مسبقاً'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': error_msg})
                messages.error(request, error_msg)
                return redirect('employees:index')
            
            if Employee.objects.filter(job_number=data['job_number']).exists():
                error_msg = 'الرقم الوظيفي موجود مسبقاً'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': error_msg})
                messages.error(request, error_msg)
                return redirect('employees:index')
            
            # Create employee with default password
            default_password = request.POST.get('password', '123456')  # Default or from form
            employee = Employee.objects.create(
                username=data['username'],
                name=data['name'],
                email=data['email'],
                job_title=data['job_title'],
                job_number=data['job_number'],
                mobile_number=data['mobile_number'],
                section=data['section'],
                notes=data['notes'],
                is_active_employee=data['is_active_employee'],
                password=make_password(default_password)
            )
            
            success_msg = f'تم إضافة الموظف {employee.name} بنجاح'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True, 
                    'message': success_msg,
                    'employee_id': employee.pk
                })
            
            messages.success(request, success_msg)
            return redirect('employees:index')
            
        except Exception as e:
            error_msg = f'حدث خطأ أثناء إضافة الموظف: {str(e)}'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': error_msg})
            messages.error(request, error_msg)
            return redirect('employees:index')
    
    # GET request - return form in modal
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        context = {
            'section_choices': Employee.SECTION_CHOICES,
            'form_action': 'create'
        }
        return render(request, 'employees/partials/employee_form_modal.html', context)
    
    return redirect('employees:index')

@login_required
@require_http_methods(["GET", "POST"])
def edit(request, pk):
    """
    Edit existing employee
    """
    employee = get_object_or_404(Employee, pk=pk)
    
    if request.method == 'POST':
        try:
            # Extract data from POST request
            data = {
                'username': request.POST.get('username'),
                'name': request.POST.get('name'),
                'email': request.POST.get('email'),
                'job_title': request.POST.get('job_title'),
                'job_number': request.POST.get('job_number'),
                'mobile_number': request.POST.get('mobile_number'),
                'section': request.POST.get('section'),
                'notes': request.POST.get('notes', ''),
                'is_active_employee': request.POST.get('is_active_employee') == 'on'
            }
            
            # Validate required fields
            required_fields = ['username', 'name', 'email', 'job_title', 'job_number', 'mobile_number', 'section']
            for field in required_fields:
                if not data.get(field):
                    error_msg = f'الحقل {field} مطلوب'
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'success': False, 'error': error_msg})
                    messages.error(request, error_msg)
                    return redirect('employees:index')
            
            # Check for unique constraints (excluding current employee)
            if Employee.objects.filter(username=data['username']).exclude(pk=employee.pk).exists():
                error_msg = 'اسم المستخدم موجود مسبقاً'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': error_msg})
                messages.error(request, error_msg)
                return redirect('employees:index')
            
            if Employee.objects.filter(email=data['email']).exclude(pk=employee.pk).exists():
                error_msg = 'البريد الإلكتروني موجود مسبقاً'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': error_msg})
                messages.error(request, error_msg)
                return redirect('employees:index')
            
            if Employee.objects.filter(job_number=data['job_number']).exclude(pk=employee.pk).exists():
                error_msg = 'الرقم الوظيفي موجود مسبقاً'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': error_msg})
                messages.error(request, error_msg)
                return redirect('employees:index')
            
            # Update employee
            for field, value in data.items():
                setattr(employee, field, value)
            
            # Update password if provided
            new_password = request.POST.get('password')
            if new_password:
                employee.password = make_password(new_password)
            
            employee.save()
            
            success_msg = f'تم تحديث بيانات الموظف {employee.name} بنجاح'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True, 
                    'message': success_msg,
                    'employee_id': employee.pk
                })
            
            messages.success(request, success_msg)
            return redirect('employees:index')
            
        except Exception as e:
            error_msg = f'حدث خطأ أثناء تحديث الموظف: {str(e)}'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': error_msg})
            messages.error(request, error_msg)
            return redirect('employees:index')
    
    # GET request - return form in modal
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        context = {
            'employee': employee,
            'section_choices': Employee.SECTION_CHOICES,
            'form_action': 'edit'
        }
        return render(request, 'employees/partials/employee_form_modal.html', context)
    
    return redirect('employees:index')

@login_required
@require_http_methods(["POST"])
def delete(request, pk):
    """
    Delete employee with confirmation
    """
    employee = get_object_or_404(Employee, pk=pk)
    
    # Check if employee can be deleted
    if not employee.can_be_deleted():
        error_msg = f'لا يمكن حذف الموظف {employee.name} لأنه مرتبط بـ: {", ".join(employee.get_deletion_blockers())}'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': error_msg})
        messages.error(request, error_msg)
        return redirect('employees:index')
    
    try:
        employee_name = employee.name
        employee.delete()
        
        success_msg = f'تم حذف الموظف {employee_name} بنجاح'
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': success_msg})
        
        messages.success(request, success_msg)
        return redirect('employees:index')
        
    except Exception as e:
        error_msg = f'حدث خطأ أثناء حذف الموظف: {str(e)}'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': error_msg})
        messages.error(request, error_msg)
        return redirect('employees:index')

@login_required
def toggle_status(request, pk):
    """
    Toggle employee active status
    """
    if request.method == 'POST':
        employee = get_object_or_404(Employee, pk=pk)
        employee.is_active_employee = not employee.is_active_employee
        employee.save()
        
        status = 'نشط' if employee.is_active_employee else 'غير نشط'
        success_msg = f'تم تغيير حالة الموظف {employee.name} إلى {status}'
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True, 
                'message': success_msg,
                'new_status': employee.is_active_employee
            })
        
        messages.success(request, success_msg)
        return redirect('employees:index')
    
    return redirect('employees:index')






# Add this to your employees/views.py file

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.conf import settings
import logging

logger = logging.getLogger('employees')

@never_cache
@csrf_protect
@require_http_methods(["GET", "POST"])
def employee_login(request):
    """
    Employee login view with enhanced security and user experience
    """
    # Redirect if user is already authenticated
    if request.user.is_authenticated:
        return redirect('dashboard:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        remember_me = request.POST.get('remember_me', False)
        
        # Basic validation
        if not username or not password:
            messages.error(request, 'يرجى إدخال اسم المستخدم وكلمة المرور')
            return render(request, 'employees/login.html')
        
        # Attempt authentication
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_active:
                # Login successful
                login(request, user)
                
                # Set session expiry based on remember me
                if remember_me:
                    # Remember for 30 days
                    request.session.set_expiry(30 * 24 * 60 * 60)
                else:
                    # Browser session only
                    request.session.set_expiry(0)
                
                # Log successful login
                logger.info(f'Successful login for user: {user.username} ({user.name})')
                
                # Success message
                messages.success(request, f'أهلاً وسهلاً، {user.name}')
                
                # Redirect to intended page or dashboard
                next_url = request.GET.get('next') or request.POST.get('next')
                if next_url:
                    return HttpResponseRedirect(next_url)
                else:
                    return redirect('dashboard:dashboard')
            else:
                # User account is disabled
                messages.error(request, 'حسابك غير مفعل. يرجى التواصل مع الإدارة')
                logger.warning(f'Login attempt for inactive user: {username}')
        else:
            # Authentication failed
            messages.error(request, 'اسم المستخدم أو كلمة المرور غير صحيحة')
            logger.warning(f'Failed login attempt for username: {username}')
    
    # GET request or failed POST
    context = {
        'title': 'تسجيل الدخول - جمعية إعمار',
        'next': request.GET.get('next', ''),
    }
    
    return render(request, 'employees/login.html', context)

@require_http_methods(["POST"])
def employee_logout(request):
    """
    Employee logout view
    """
    if request.user.is_authenticated:
        username = request.user.username
        name = request.user.name
        
        # Log logout
        logger.info(f'User logged out: {username} ({name})')
        
        # Logout user
        logout(request)
        
        # Success message
        messages.success(request, 'تم تسجيل الخروج بنجاح')
    
    return redirect('employees:login')

def password_reset_request(request):
    """
    Password reset request view (placeholder for future implementation)
    """
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        
        if not email:
            messages.error(request, 'يرجى إدخال البريد الإلكتروني')
            return render(request, 'employees/password_reset.html')
        
        # TODO: Implement password reset logic
        messages.info(request, 'سيتم إرسال رابط إعادة تعيين كلمة المرور إلى بريدك الإلكتروني قريباً')
        
        return redirect('employees:login')
    
    return render(request, 'employees/password_reset.html')

# Additional utility functions for login security

def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def is_safe_url(url, allowed_hosts=None):
    """
    Check if a URL is safe for redirection
    """
    if not url:
        return False
    
    if url.startswith('//') or url.startswith('http'):
        return False
    
    return True






from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
from django.http import HttpResponseRedirect
from django.urls import reverse
import logging

logger = logging.getLogger('employees')

@never_cache
@csrf_protect
@require_http_methods(["GET", "POST"])
def custom_login(request):
    """
    Custom login view that renders your login.html template
    """
    # Redirect if user is already authenticated
    if request.user.is_authenticated:
        return redirect('dashboard:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        remember_me = request.POST.get('remember_me', False)
        
        # Basic validation
        if not username or not password:
            messages.error(request, 'يرجى إدخال اسم المستخدم وكلمة المرور')
            return render(request, 'employees/login.html')
        
        # Attempt authentication
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_active:
                # Login successful
                login(request, user)
                
                # Set session expiry based on remember me
                if remember_me:
                    # Remember for 30 days
                    request.session.set_expiry(30 * 24 * 60 * 60)
                else:
                    # Browser session only
                    request.session.set_expiry(0)
                
                # Log successful login
                logger.info(f'Successful login for user: {user.username} ({user.name})')
                
                # Success message
                messages.success(request, f'أهلاً وسهلاً، {user.name}')
                
                # Redirect to intended page or dashboard
                next_url = request.GET.get('next') or request.POST.get('next')
                if next_url and next_url.startswith('/'):
                    return HttpResponseRedirect(next_url)
                else:
                    return redirect('dashboard:dashboard')
            else:
                # User account is disabled
                messages.error(request, 'حسابك غير مفعل. يرجى التواصل مع الإدارة')
                logger.warning(f'Login attempt for inactive user: {username}')
        else:
            # Authentication failed
            messages.error(request, 'اسم المستخدم أو كلمة المرور غير صحيحة')
            logger.warning(f'Failed login attempt for username: {username}')
    
    # GET request or failed POST
    context = {
        'title': 'تسجيل الدخول - جمعية إعمار',
        'next': request.GET.get('next', ''),
    }
    
    return render(request, 'employees/login.html', context)

@require_http_methods(["POST", "GET"])
def custom_logout(request):
    """
    Custom logout view that redirects to your login page
    """
    if request.user.is_authenticated:
        username = request.user.username
        name = getattr(request.user, 'name', username)
        
        # Log logout
        logger.info(f'User logged out: {username} ({name})')
        
        # Logout user
        logout(request)
        
        # Success message
        messages.success(request, 'تم تسجيل الخروج بنجاح')
    
    # Redirect to your custom login page
    return redirect('employees:login')
