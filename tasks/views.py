from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Project, Task
from datetime import datetime
from .models import MonthlyGoal


from django.db.models import Q, Count, Case, When, IntegerField
from .models import Task, Project


Employee = get_user_model()

# ====== TASK VIEWS ======

@login_required
def my_tasks(request):
    """
    My Tasks view - shows tasks created by user and tasks assigned to user
    """
    # Section 1: Tasks created by me (not assigned to anyone) + Tasks assigned to me
    my_unassigned_tasks = Task.objects.filter(
        created_by=request.user,
        assigned_to__isnull=True,
        status='new'
    ).select_related('project', 'created_by')
    
    assigned_to_me_tasks = Task.objects.filter(
        assigned_to=request.user,
        status='new'
    ).select_related('project', 'created_by', 'assigned_to')
    
    # Section 2: Tasks created by me and assigned to others
    my_assigned_tasks = Task.objects.filter(
        created_by=request.user,
        assigned_to__isnull=False,
        status='new'
    ).select_related('project', 'created_by', 'assigned_to')
    
    # Apply filters to each section
    search_query = request.GET.get('search', '')
    project_filter = request.GET.get('project', '')
    assigned_filter = request.GET.get('assigned', '')
    
    if search_query:
        search_q = Q(name__icontains=search_query) | Q(detail__icontains=search_query)
        my_unassigned_tasks = my_unassigned_tasks.filter(search_q)
        assigned_to_me_tasks = assigned_to_me_tasks.filter(search_q)
        my_assigned_tasks = my_assigned_tasks.filter(search_q)
    
    if project_filter:
        project_q = Q(project_id=project_filter)
        my_unassigned_tasks = my_unassigned_tasks.filter(project_q)
        assigned_to_me_tasks = assigned_to_me_tasks.filter(project_q)
        my_assigned_tasks = my_assigned_tasks.filter(project_q)
    
    if assigned_filter:
        assigned_q = Q(assigned_to_id=assigned_filter)
        my_assigned_tasks = my_assigned_tasks.filter(assigned_q)
    
    # Get related data for filters
    projects = Project.objects.all().order_by('name')
    employees = Employee.objects.filter(is_active_employee=True).order_by('name')
    
    # Calculate statistics
    total_my_tasks = Task.objects.filter(
        Q(created_by=request.user) | Q(assigned_to=request.user)
    ).count()
    
    my_created_tasks = Task.objects.filter(created_by=request.user).count()
    my_active_tasks = Task.objects.filter(
        Q(created_by=request.user) | Q(assigned_to=request.user),
        status='new'
    ).count()
    overdue_tasks = Task.objects.filter(
        Q(created_by=request.user) | Q(assigned_to=request.user),
        status='new',
        due_date__lt=timezone.now().date()
    ).count()
    
    context = {
        'title': 'مهامي',
        'current_page': 'my_tasks',
        'my_unassigned_tasks': my_unassigned_tasks,
        'assigned_to_me_tasks': assigned_to_me_tasks,
        'my_assigned_tasks': my_assigned_tasks,
        'search_query': search_query,
        'project_filter': project_filter,
        'assigned_filter': assigned_filter,
        'projects': projects,
        'employees': employees,
        'total_my_tasks': total_my_tasks,
        'my_created_tasks': my_created_tasks,
        'my_active_tasks': my_active_tasks,
        'overdue_tasks': overdue_tasks,
    }
    
    return render(request, 'tasks/my_tasks.html', context)

@login_required
def finished_tasks(request):
    """
    Display finished tasks with filters
    """
    tasks = Task.objects.filter(
        Q(created_by=request.user) | Q(assigned_to=request.user),
        status='finished'
    ).select_related('project', 'created_by', 'assigned_to')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        tasks = tasks.filter(
            Q(name__icontains=search_query) |
            Q(detail__icontains=search_query)
        )
    
    # Filter by project
    project_filter = request.GET.get('project', '')
    if project_filter:
        tasks = tasks.filter(project_id=project_filter)
    
    # Filter by creator
    creator_filter = request.GET.get('creator', '')
    if creator_filter:
        tasks = tasks.filter(created_by_id=creator_filter)
    
    # Filter by assigned user
    assigned_filter = request.GET.get('assigned', '')
    if assigned_filter:
        tasks = tasks.filter(assigned_to_id=assigned_filter)
    
    # إضافة معلومات الصلاحيات لكل مهمة
    task_list = []
    for task in tasks:
        task.can_change_status_by = task.can_change_status_by(request.user)
        task.can_be_edited_by = task.can_be_edited_by(request.user)
        task.can_be_deleted_by = task.can_be_deleted_by(request.user)
        task_list.append(task)
    
    # Pagination
    paginator = Paginator(task_list, 15)  # 15 tasks per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get related data for filters
    projects = Project.objects.all().order_by('name')
    creators = Employee.objects.filter(
        created_tasks__status='finished'
    ).distinct().order_by('name')
    assigned_users = Employee.objects.filter(
        assigned_tasks__status='finished'
    ).distinct().order_by('name')
    
    context = {
        'title': 'المهام المكتملة',
        'current_page': 'my_tasks',
        'page_obj': page_obj,
        'search_query': search_query,
        'project_filter': project_filter,
        'creator_filter': creator_filter,
        'assigned_filter': assigned_filter,
        'projects': projects,
        'creators': creators,
        'assigned_users': assigned_users,
        'total_finished': len(task_list),
    }
    
    return render(request, 'tasks/finished_tasks.html', context)



@login_required
def task_detail(request, pk):
    """
    Display task detail
    """
    task = get_object_or_404(Task.objects.select_related('project', 'created_by', 'assigned_to'), pk=pk)
    
    # Check if request is AJAX for modal display
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        context = {
            'task': task,
            'can_edit': task.can_be_edited_by(request.user),
            'can_delete': task.can_be_deleted_by(request.user),
            'can_change_status': task.can_change_status_by(request.user),
        }
        # تأكد من المسار الصحيح
        return render(request, 'tasks/partials/task_detail_modal.html', context)
    
    # إذا لم يكن AJAX request
    return redirect('tasks:my_tasks')


# في ملف tasks/views.py - تأكد من أن create_task view يبدو هكذا:
@login_required
@require_http_methods(["GET", "POST"])
def create_task(request):
    """
    Create new task
    """
    print(f"create_task called with method: {request.method}")  # للتشخيص
    print(f"Is AJAX: {request.headers.get('X-Requested-With') == 'XMLHttpRequest'}")  # للتشخيص
    
    if request.method == 'POST':
        # معالجة إنشاء المهمة
        try:
            data = {
                'name': request.POST.get('name'),
                'detail': request.POST.get('detail', ''),
                'due_date': request.POST.get('due_date') or None,
                'project_id': request.POST.get('project') or None,
                'assigned_to_id': request.POST.get('assigned_to') or None,
                'status': request.POST.get('status', 'new'),
            }
            
            if not data['name']:
                error_msg = 'اسم المهمة مطلوب'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': error_msg})
                messages.error(request, error_msg)
                return redirect('tasks:my_tasks')
            
            # Validate project if provided
            project = None
            if data['project_id']:
                try:
                    project = Project.objects.get(pk=data['project_id'])
                except Project.DoesNotExist:
                    error_msg = 'المشروع المحدد غير موجود'
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'success': False, 'error': error_msg})
                    messages.error(request, error_msg)
                    return redirect('tasks:my_tasks')
            
            # Validate assigned user if provided
            assigned_to = None
            if data['assigned_to_id']:
                try:
                    assigned_to = Employee.objects.get(
                        pk=data['assigned_to_id'],
                        is_active_employee=True
                    )
                except Employee.DoesNotExist:
                    error_msg = 'الموظف المحدد غير موجود أو غير نشط'
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'success': False, 'error': error_msg})
                    messages.error(request, error_msg)
                    return redirect('tasks:my_tasks')
            
            # Create task
            task = Task.objects.create(
                name=data['name'],
                detail=data['detail'],
                due_date=data['due_date'],
                project=project,
                assigned_to=assigned_to,
                status=data['status'],
                created_by=request.user
            )
            
            success_msg = f'تم إنشاء المهمة "{task.name}" بنجاح'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True, 
                    'message': success_msg,
                    'task_id': task.pk
                })
            
            messages.success(request, success_msg)
            return redirect('tasks:my_tasks')
            
        except Exception as e:
            error_msg = f'حدث خطأ أثناء إنشاء المهمة: {str(e)}'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': error_msg})
            messages.error(request, error_msg)
            return redirect('tasks:my_tasks')
    
    # GET request - return form in modal
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        print("Returning task form modal")  # للتشخيص
        projects = Project.objects.all().order_by('name')
        employees = Employee.objects.filter(is_active_employee=True).order_by('name')
        context = {
            'status_choices': Task.STATUS_CHOICES,
            'projects': projects,
            'employees': employees,
            'form_action': 'create',  # هذا مهم جداً!
            'today': timezone.now().date()
        }
        # تأكد من اسم الملف الصحيح
        return render(request, 'tasks/partials/task_form_modal.html', context)
    else:
        print("Not AJAX request, redirecting")  # للتشخيص
    
    return redirect('tasks:my_tasks')


@login_required
@require_http_methods(["GET", "POST"])
def edit_task(request, pk):
    """
    Edit existing task
    """
    task = get_object_or_404(Task.objects.select_related('project', 'created_by', 'assigned_to'), pk=pk)
    
    # Check permissions
    if not task.can_be_edited_by(request.user):
        error_msg = 'ليس لديك صلاحية لتعديل هذه المهمة'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': error_msg})
        messages.error(request, error_msg)
        return redirect('tasks:my_tasks')
    
    if request.method == 'POST':
        try:
            # Extract data from POST request
            data = {
                'name': request.POST.get('name'),
                'detail': request.POST.get('detail', ''),
                'due_date': request.POST.get('due_date') or None,
                'project_id': request.POST.get('project') or None,
                'assigned_to_id': request.POST.get('assigned_to') or None,
                'status': request.POST.get('status', 'new'),
            }
            
            # Validate required fields
            if not data['name']:
                error_msg = 'اسم المهمة مطلوب'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': error_msg})
                messages.error(request, error_msg)
                return redirect('tasks:my_tasks')
            
            # Validate project if provided
            project = None
            if data['project_id']:
                try:
                    project = Project.objects.get(pk=data['project_id'])
                except Project.DoesNotExist:
                    error_msg = 'المشروع المحدد غير موجود'
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'success': False, 'error': error_msg})
                    messages.error(request, error_msg)
                    return redirect('tasks:my_tasks')
            
            # Validate assigned user if provided
            assigned_to = None
            if data['assigned_to_id']:
                try:
                    assigned_to = Employee.objects.get(
                        pk=data['assigned_to_id'],
                        is_active_employee=True
                    )
                except Employee.DoesNotExist:
                    error_msg = 'الموظف المحدد غير موجود أو غير نشط'
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'success': False, 'error': error_msg})
                    messages.error(request, error_msg)
                    return redirect('tasks:my_tasks')
            
            # Update task
            task.name = data['name']
            task.detail = data['detail']
            task.due_date = data['due_date']
            task.project = project
            task.assigned_to = assigned_to
            task.status = data['status']
            task.save()
            
            success_msg = f'تم تحديث المهمة "{task.name}" بنجاح'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True, 
                    'message': success_msg,
                    'task_id': task.pk
                })
            
            messages.success(request, success_msg)
            return redirect('tasks:my_tasks')
            
        except Exception as e:
            error_msg = f'حدث خطأ أثناء تحديث المهمة: {str(e)}'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': error_msg})
            messages.error(request, error_msg)
            return redirect('tasks:my_tasks')
    
    # GET request - return form in modal
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        projects = Project.objects.all().order_by('name')
        employees = Employee.objects.filter(is_active_employee=True).order_by('name')
        context = {
            'task': task,
            'status_choices': Task.STATUS_CHOICES,
            'projects': projects,
            'employees': employees,
            'form_action': 'edit',
            'today': timezone.now().date()
        }
        return render(request, 'tasks/partials/task_form_modal.html', context)
    
    return redirect('tasks:my_tasks')

@login_required
@require_http_methods(["POST"])
def delete_task(request, pk):
    """
    Delete task with confirmation
    """
    task = get_object_or_404(Task, pk=pk)
    
    # Check permissions
    if not task.can_be_deleted_by(request.user):
        error_msg = 'ليس لديك صلاحية لحذف هذه المهمة'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': error_msg})
        messages.error(request, error_msg)
        return redirect('tasks:my_tasks')
    
    try:
        task_name = task.name
        task.delete()
        
        success_msg = f'تم حذف المهمة "{task_name}" بنجاح'
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': success_msg})
        
        messages.success(request, success_msg)
        return redirect('tasks:my_tasks')
        
    except Exception as e:
        error_msg = f'حدث خطأ أثناء حذف المهمة: {str(e)}'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': error_msg})
        messages.error(request, error_msg)
        return redirect('tasks:my_tasks')

@login_required
@require_http_methods(["POST"])
def toggle_task_status(request, pk):
    """
    Toggle task status between new and finished
    """
    task = get_object_or_404(Task, pk=pk)
    
    # Check permissions
    if not task.can_change_status_by(request.user):
        error_msg = 'ليس لديك صلاحية لتغيير حالة هذه المهمة'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': error_msg})
        messages.error(request, error_msg)
        return redirect('tasks:my_tasks')
    
    try:
        # Toggle status
        task.status = 'finished' if task.status == 'new' else 'new'
        task.save()
        
        status_text = 'مكتملة' if task.status == 'finished' else 'جديدة'
        success_msg = f'تم تغيير حالة المهمة "{task.name}" إلى {status_text}'
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True, 
                'message': success_msg,
                'new_status': task.status,
                'status_display': task.get_status_display_arabic()
            })
        
        messages.success(request, success_msg)
        return redirect('tasks:my_tasks')
        
    except Exception as e:
        error_msg = f'حدث خطأ أثناء تغيير حالة المهمة: {str(e)}'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': error_msg})
        messages.error(request, error_msg)
        return redirect('tasks:my_tasks')


# ====== PROJECT VIEWS ======

@login_required
def projects(request):
    """
    Display all projects with search and filter functionality
    """
    projects = Project.objects.prefetch_related('assigned_employees', 'created_by').all()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        projects = projects.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(assigned_employees__name__icontains=search_query) |
            Q(primary_assigned_employee__name__icontains=search_query) |
            Q(created_by__name__icontains=search_query)
        ).distinct()
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        projects = projects.filter(status=status_filter)
    
    # Filter by assigned employee
    employee_filter = request.GET.get('employee', '')
    if employee_filter:
        projects = projects.filter(
            Q(assigned_employees__id=employee_filter) |
            Q(primary_assigned_employee__id=employee_filter)
        ).distinct()
    
    # Filter by overdue
    overdue_filter = request.GET.get('overdue', '')
    if overdue_filter == 'true':
        today = timezone.now().date()
        projects = projects.filter(
            due_date__lt=today,
            status__in=['new', 'in_progress']
        )
    
    # Pagination
    paginator = Paginator(projects, 12)  # 12 projects per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get employees for filter dropdown
    employees = Employee.objects.filter(is_active_employee=True).order_by('name')
    
    # Calculate statistics
    total_projects = Project.objects.count()
    new_projects = Project.objects.filter(status='new').count()
    in_progress_projects = Project.objects.filter(status='in_progress').count()
    finished_projects = Project.objects.filter(status='finished').count()
    overdue_projects = Project.objects.filter(
        due_date__lt=timezone.now().date(),
        status__in=['new', 'in_progress']
    ).count()
    
    context = {
        'title': 'المشاريع',
        'current_page': 'projects',
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'employee_filter': employee_filter,
        'overdue_filter': overdue_filter,
        'status_choices': Project.STATUS_CHOICES,
        'employees': employees,
        'total_projects': total_projects,
        'new_projects': new_projects,
        'in_progress_projects': in_progress_projects,
        'finished_projects': finished_projects,
        'overdue_projects': overdue_projects,
    }
    
    return render(request, 'tasks/projects/index.html', context)

@login_required
def project_detail(request, pk):
    """
    Display project detail
    """
    project = get_object_or_404(Project.objects.prefetch_related('assigned_employees'), pk=pk)
    
    # Check if request is AJAX for modal display
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        context = {
            'project': project,
            'can_delete': project.can_be_deleted(),
            'deletion_blockers': project.get_deletion_blockers() if not project.can_be_deleted() else []
        }
        return render(request, 'tasks/projects/partials/project_detail_modal.html', context)
    
    context = {
        'title': f'تفاصيل المشروع - {project.name}',
        'current_page': 'projects',
        'project': project,
        'can_delete': project.can_be_deleted(),
        'deletion_blockers': project.get_deletion_blockers() if not project.can_be_deleted() else []
    }
    
    return render(request, 'tasks/projects/detail.html', context)

@login_required
@require_http_methods(["GET", "POST"])
def create_project(request):
    """
    Create new project with multiple employees support
    """
    if request.method == 'POST':
        try:
            # Extract data from POST request
            data = {
                'name': request.POST.get('name'),
                'description': request.POST.get('description', ''),
                'assigned_employees': request.POST.getlist('assigned_employees'),
                'primary_assigned_employee_id': request.POST.get('primary_assigned_employee') or None,
                'due_date': request.POST.get('due_date') or None,
                'status': request.POST.get('status', 'new'),
            }
            
            # Validate required fields
            if not data['name']:
                error_msg = 'اسم المشروع مطلوب'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': error_msg})
                messages.error(request, error_msg)
                return redirect('tasks:projects')
            
            # Check for duplicate project names
            if Project.objects.filter(name=data['name']).exists():
                error_msg = 'اسم المشروع موجود مسبقاً'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': error_msg})
                messages.error(request, error_msg)
                return redirect('tasks:projects')
            
            # Validate assigned employees
            assigned_employees = []
            if data['assigned_employees']:
                try:
                    assigned_employees = Employee.objects.filter(
                        pk__in=data['assigned_employees'],
                        is_active_employee=True
                    )
                    if assigned_employees.count() != len(data['assigned_employees']):
                        error_msg = 'بعض الموظفين المحددين غير موجودين أو غير نشطين'
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            return JsonResponse({'success': False, 'error': error_msg})
                        messages.error(request, error_msg)
                        return redirect('tasks:projects')
                except ValueError:
                    error_msg = 'معرفات الموظفين غير صحيحة'
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'success': False, 'error': error_msg})
                    messages.error(request, error_msg)
                    return redirect('tasks:projects')
            
            # Validate primary assigned employee
            primary_assigned_employee = None
            if data['primary_assigned_employee_id']:
                try:
                    primary_assigned_employee = Employee.objects.get(
                        pk=data['primary_assigned_employee_id'],
                        is_active_employee=True
                    )
                    # Check if primary employee is in assigned employees list
                    if data['assigned_employees'] and str(primary_assigned_employee.pk) not in data['assigned_employees']:
                        error_msg = 'الموظف الرئيسي يجب أن يكون من ضمن الموظفين المُعيّنين'
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            return JsonResponse({'success': False, 'error': error_msg})
                        messages.error(request, error_msg)
                        return redirect('tasks:projects')
                except Employee.DoesNotExist:
                    error_msg = 'الموظف الرئيسي المحدد غير موجود أو غير نشط'
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'success': False, 'error': error_msg})
                    messages.error(request, error_msg)
                    return redirect('tasks:projects')
            
            # Create project
            project = Project.objects.create(
                name=data['name'],
                description=data['description'],
                primary_assigned_employee=primary_assigned_employee,
                due_date=data['due_date'],
                status=data['status'],
                created_by=request.user
            )
            
            # Add assigned employees
            if assigned_employees:
                project.assigned_employees.set(assigned_employees)
            
            success_msg = f'تم إنشاء المشروع "{project.name}" بنجاح'
            if assigned_employees:
                success_msg += f' وتم تعيين {assigned_employees.count()} موظف'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True, 
                    'message': success_msg,
                    'project_id': project.pk
                })
            
            messages.success(request, success_msg)
            return redirect('tasks:projects')
            
        except Exception as e:
            error_msg = f'حدث خطأ أثناء إنشاء المشروع: {str(e)}'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': error_msg})
            messages.error(request, error_msg)
            return redirect('tasks:projects')
    
    # GET request - return form in modal
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        employees = Employee.objects.filter(is_active_employee=True).order_by('name')
        context = {
            'status_choices': Project.STATUS_CHOICES,
            'employees': employees,
            'form_action': 'create',
            'today': timezone.now().date()
        }
        return render(request, 'tasks/projects/partials/project_form_modal.html', context)
    
    return redirect('tasks:projects')

@login_required
@require_http_methods(["GET", "POST"])
def edit_project(request, pk):
    """
    Edit existing project with multiple employees support
    """
    project = get_object_or_404(Project.objects.prefetch_related('assigned_employees'), pk=pk)
    
    if request.method == 'POST':
        try:
            # Extract data from POST request
            data = {
                'name': request.POST.get('name'),
                'description': request.POST.get('description', ''),
                'assigned_employees': request.POST.getlist('assigned_employees'),
                'primary_assigned_employee_id': request.POST.get('primary_assigned_employee') or None,
                'due_date': request.POST.get('due_date') or None,
                'status': request.POST.get('status', 'new'),
            }
            
            # Validate required fields
            if not data['name']:
                error_msg = 'اسم المشروع مطلوب'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': error_msg})
                messages.error(request, error_msg)
                return redirect('tasks:projects')
            
            # Check for duplicate project names (excluding current project)
            if Project.objects.filter(name=data['name']).exclude(pk=project.pk).exists():
                error_msg = 'اسم المشروع موجود مسبقاً'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': error_msg})
                messages.error(request, error_msg)
                return redirect('tasks:projects')
            
            # Validate assigned employees
            assigned_employees = []
            if data['assigned_employees']:
                try:
                    assigned_employees = Employee.objects.filter(
                        pk__in=data['assigned_employees'],
                        is_active_employee=True
                    )
                    if assigned_employees.count() != len(data['assigned_employees']):
                        error_msg = 'بعض الموظفين المحددين غير موجودين أو غير نشطين'
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            return JsonResponse({'success': False, 'error': error_msg})
                        messages.error(request, error_msg)
                        return redirect('tasks:projects')
                except ValueError:
                    error_msg = 'معرفات الموظفين غير صحيحة'
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'success': False, 'error': error_msg})
                    messages.error(request, error_msg)
                    return redirect('tasks:projects')
            
            # Validate primary assigned employee
            primary_assigned_employee = None
            if data['primary_assigned_employee_id']:
                try:
                    primary_assigned_employee = Employee.objects.get(
                        pk=data['primary_assigned_employee_id'],
                        is_active_employee=True
                    )
                    # Check if primary employee is in assigned employees list
                    if data['assigned_employees'] and str(primary_assigned_employee.pk) not in data['assigned_employees']:
                        error_msg = 'الموظف الرئيسي يجب أن يكون من ضمن الموظفين المُعيّنين'
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            return JsonResponse({'success': False, 'error': error_msg})
                        messages.error(request, error_msg)
                        return redirect('tasks:projects')
                except Employee.DoesNotExist:
                    error_msg = 'الموظف الرئيسي المحدد غير موجود أو غير نشط'
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'success': False, 'error': error_msg})
                    messages.error(request, error_msg)
                    return redirect('tasks:projects')
            
            # Update project
            project.name = data['name']
            project.description = data['description']
            project.primary_assigned_employee = primary_assigned_employee
            project.due_date = data['due_date']
            project.status = data['status']
            project.save()
            
            # Update assigned employees
            if assigned_employees:
                project.assigned_employees.set(assigned_employees)
            else:
                project.assigned_employees.clear()
            
            success_msg = f'تم تحديث المشروع "{project.name}" بنجاح'
            if assigned_employees:
                success_msg += f' مع {assigned_employees.count()} موظف مُعيّن'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True, 
                    'message': success_msg,
                    'project_id': project.pk
                })
            
            messages.success(request, success_msg)
            return redirect('tasks:projects')
            
        except Exception as e:
            error_msg = f'حدث خطأ أثناء تحديث المشروع: {str(e)}'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': error_msg})
            messages.error(request, error_msg)
            return redirect('tasks:projects')
    
    # GET request - return form in modal
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        employees = Employee.objects.filter(is_active_employee=True).order_by('name')
        context = {
            'project': project,
            'status_choices': Project.STATUS_CHOICES,
            'employees': employees,
            'form_action': 'edit',
            'today': timezone.now().date()
        }
        return render(request, 'tasks/projects/partials/project_form_modal.html', context)
    
    return redirect('tasks:projects')

@login_required
@require_http_methods(["POST"])
def delete_project(request, pk):
    """
    Delete project with confirmation
    """
    project = get_object_or_404(Project, pk=pk)
    
    # Check if project can be deleted
    if not project.can_be_deleted():
        error_msg = f'لا يمكن حذف المشروع "{project.name}" لأنه مرتبط بـ: {", ".join(project.get_deletion_blockers())}'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': error_msg})
        messages.error(request, error_msg)
        return redirect('tasks:projects')
    
    try:
        project_name = project.name
        project.delete()
        
        success_msg = f'تم حذف المشروع "{project_name}" بنجاح'
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': success_msg})
        
        messages.success(request, success_msg)
        return redirect('tasks:projects')
        
    except Exception as e:
        error_msg = f'حدث خطأ أثناء حذف المشروع: {str(e)}'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': error_msg})
        messages.error(request, error_msg)
        return redirect('tasks:projects')
    










# Add these views to tasks/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from datetime import datetime
from .models import MonthlyGoal

Employee = get_user_model()

@login_required
def monthly_goals_index(request):
    """
    Display monthly goals for the current user
    """
    # Get current user's monthly goals
    monthly_goals = MonthlyGoal.objects.filter(employee=request.user)
    
    # Get statistics
    total_goals = monthly_goals.count()
    current_year = datetime.now().year
    current_year_goals = monthly_goals.filter(year=current_year).count()
    
    context = {
        'title': 'أهداف الشهر',
        'current_page': 'monthly_goals',
        'monthly_goals': monthly_goals,
        'total_goals': total_goals,
        'current_year_goals': current_year_goals,
        'current_year': current_year,
        'month_choices': MonthlyGoal.MONTH_CHOICES,
    }
    
    return render(request, 'tasks/monthly_goals.html', context)


@login_required
def monthly_goals_detail(request, pk):
    """
    Display monthly goal details
    """
    monthly_goal = get_object_or_404(MonthlyGoal, pk=pk, employee=request.user)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        context = {
            'monthly_goal': monthly_goal,
            'can_edit': monthly_goal.can_be_edited_by(request.user),
            'can_delete': monthly_goal.can_be_deleted_by(request.user),
        }
        return render(request, 'tasks/partials/monthly_goal_detail_modal.html', context)
    
    context = {
        'title': f'أهداف {monthly_goal.month_year_display}',
        'current_page': 'monthly_goals',
        'monthly_goal': monthly_goal,
        'can_edit': monthly_goal.can_be_edited_by(request.user),
        'can_delete': monthly_goal.can_be_deleted_by(request.user),
    }
    
    return render(request, 'tasks/monthly_goal_detail.html', context)

@login_required
@require_http_methods(["GET", "POST"])
def monthly_goals_edit(request, pk):
    """
    Edit existing monthly goal
    """
    monthly_goal = get_object_or_404(MonthlyGoal, pk=pk, employee=request.user)
    
    if not monthly_goal.can_be_edited_by(request.user):
        error_msg = 'ليس لديك صلاحية لتعديل هذه الأهداف'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': error_msg})
        messages.error(request, error_msg)
        return redirect('tasks:monthly_goals')
    
    if request.method == 'POST':
        try:
            month = int(request.POST.get('month'))
            year = int(request.POST.get('year'))
            goals = request.POST.get('goals', '').strip()
            
            # Validation
            if not goals:
                error_msg = 'يجب إدخال الأهداف'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': error_msg})
                messages.error(request, error_msg)
                return redirect('tasks:monthly_goals')
            
            if not (1 <= month <= 12):
                error_msg = 'الشهر غير صحيح'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': error_msg})
                messages.error(request, error_msg)
                return redirect('tasks:monthly_goals')
            
            # Check if another goal exists for this month/year (excluding current)
            if MonthlyGoal.objects.filter(
                employee=request.user, 
                month=month, 
                year=year
            ).exclude(pk=monthly_goal.pk).exists():
                error_msg = f'يوجد أهداف أخرى مسجلة لشهر {dict(MonthlyGoal.MONTH_CHOICES)[month]} {year}'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': error_msg})
                messages.error(request, error_msg)
                return redirect('tasks:monthly_goals')
            
            # Update monthly goal
            monthly_goal.month = month
            monthly_goal.year = year
            monthly_goal.goals = goals
            monthly_goal.save()
            
            success_msg = f'تم تحديث أهداف شهر {monthly_goal.month_name} {year} بنجاح'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': success_msg,
                    'goal_id': monthly_goal.pk
                })
            
            messages.success(request, success_msg)
            return redirect('tasks:monthly_goals')
            
        except Exception as e:
            error_msg = f'حدث خطأ أثناء تحديث الأهداف: {str(e)}'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': error_msg})
            messages.error(request, error_msg)
            return redirect('tasks:monthly_goals')
    
    # GET request - return form in modal
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        current_year = datetime.now().year
        current_month = datetime.now().month
        year_range = list(range(current_year - 2, current_year + 6))
        
        context = {
            'monthly_goal': monthly_goal,
            'month_choices': MonthlyGoal.MONTH_CHOICES,
            'current_year': current_year,
            'current_month': current_month,
            'year_range': year_range,
            'form_action': 'edit'
        }
        return render(request, 'tasks/partials/monthly_goal_form_modal.html', context)
    
    return redirect('tasks:monthly_goals')

@login_required
@require_http_methods(["POST"])
def monthly_goals_delete(request, pk):
    """
    Delete monthly goal with confirmation
    """
    monthly_goal = get_object_or_404(MonthlyGoal, pk=pk, employee=request.user)
    
    if not monthly_goal.can_be_deleted_by(request.user):
        error_msg = 'ليس لديك صلاحية لحذف هذه الأهداف'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': error_msg})
        messages.error(request, error_msg)
        return redirect('tasks:monthly_goals')
    
    try:
        goal_name = monthly_goal.month_year_display
        monthly_goal.delete()
        
        success_msg = f'تم حذف أهداف {goal_name} بنجاح'
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': success_msg})
        
        messages.success(request, success_msg)
        return redirect('tasks:monthly_goals')
        
    except Exception as e:
        error_msg = f'حدث خطأ أثناء حذف الأهداف: {str(e)}'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': error_msg})
        messages.error(request, error_msg)
        return redirect('tasks:monthly_goals')
    





@login_required
@require_http_methods(["GET", "POST"])
def monthly_goals_create(request):
    """
    Create new monthly goal
    """
    if request.method == 'POST':
        try:
            month = int(request.POST.get('month'))
            year = int(request.POST.get('year', datetime.now().year))
            goals = request.POST.get('goals', '').strip()
            
            # Validation
            if not goals:
                error_msg = 'يجب إدخال الأهداف'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': error_msg})
                messages.error(request, error_msg)
                return redirect('tasks:monthly_goals')
            
            if not (1 <= month <= 12):
                error_msg = 'الشهر غير صحيح'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': error_msg})
                messages.error(request, error_msg)
                return redirect('tasks:monthly_goals')
            
            # Check if goal already exists for this month/year
            if MonthlyGoal.objects.filter(employee=request.user, month=month, year=year).exists():
                error_msg = f'يوجد أهداف مسجلة مسبقاً لشهر {dict(MonthlyGoal.MONTH_CHOICES)[month]} {year}'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': error_msg})
                messages.error(request, error_msg)
                return redirect('tasks:monthly_goals')
            
            # Create monthly goal
            monthly_goal = MonthlyGoal.objects.create(
                employee=request.user,
                month=month,
                year=year,
                goals=goals
            )
            
            success_msg = f'تم إضافة أهداف شهر {monthly_goal.month_name} {year} بنجاح'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': success_msg,
                    'goal_id': monthly_goal.pk
                })
            
            messages.success(request, success_msg)
            return redirect('tasks:monthly_goals')
            
        except Exception as e:
            error_msg = f'حدث خطأ أثناء إضافة الأهداف: {str(e)}'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': error_msg})
            messages.error(request, error_msg)
            return redirect('tasks:monthly_goals')
    
    # GET request - return form in modal
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        current_year = datetime.now().year
        current_month = datetime.now().month
        year_range = list(range(current_year - 2, current_year + 6))
        
        context = {
            'month_choices': MonthlyGoal.MONTH_CHOICES,
            'current_year': current_year,
            'current_month': current_month,
            'year_range': year_range,
            'form_action': 'create'
        }
        return render(request, 'tasks/partials/monthly_goal_form_modal.html', context)
    
    return redirect('tasks:monthly_goals')
    """
    Create new monthly goal - Debug version
    """
    if request.method == 'POST':
        # Handle POST request (same as before)
        pass
    
    # GET request - return form in modal
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        print("AJAX request received for create form")  # Debug line
        
        current_year = datetime.now().year
        current_month = datetime.now().month
        year_range = list(range(current_year - 2, current_year + 6))
        
        context = {
            'month_choices': MonthlyGoal.MONTH_CHOICES,
            'current_year': current_year,
            'current_month': current_month,
            'year_range': year_range,
            'form_action': 'create'
        }
        
        print(f"Context: {context}")  # Debug line
        
        try:
            return render(request, 'tasks/partials/monthly_goal_form_modal.html', context)
        except Exception as e:
            print(f"Template error: {e}")  # Debug line
            return JsonResponse({'error': str(e)})
    
    print("Not an AJAX request, redirecting")  # Debug line
    return redirect('tasks:monthly_goals')





# Add these views to your existing tasks/views.py file

Employee = get_user_model()

@login_required
def employee_tasks_list(request):
    """
    Display all employees in cards format - view only
    Shows employee cards and when clicked shows their tasks
    """
    # Get all active employees with task counts
    employees = Employee.objects.filter(
        is_active_employee=True
    ).annotate(
        total_tasks=Count('assigned_tasks') + Count('created_tasks'),
        finished_tasks=Count(
            Case(
                When(Q(assigned_tasks__status='finished') | Q(created_tasks__status='finished'), then=1),
                output_field=IntegerField()
            )
        ),
        pending_tasks=Count(
            Case(
                When(Q(assigned_tasks__status='new') | Q(created_tasks__status='new'), then=1),
                output_field=IntegerField()
            )
        )
    ).order_by('name')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        employees = employees.filter(
            Q(name__icontains=search_query) |
            Q(job_title__icontains=search_query) |
            Q(job_number__icontains=search_query)
        )
    
    # Filter by section
    section_filter = request.GET.get('section', '')
    if section_filter:
        employees = employees.filter(section=section_filter)
    
    # Pagination
    paginator = Paginator(employees, 12)  # 12 employees per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get section choices for filter
    section_choices = Employee.SECTION_CHOICES
    
    # Statistics
    total_employees = Employee.objects.filter(is_active_employee=True).count()
    employees_with_tasks = Employee.objects.filter(
        Q(assigned_tasks__isnull=False) | Q(created_tasks__isnull=False),
        is_active_employee=True
    ).distinct().count()
    
    context = {
        'title': 'مهام الموظفين',
        'current_page': 'employee_tasks',
        'page_obj': page_obj,
        'search_query': search_query,
        'section_filter': section_filter,
        'section_choices': section_choices,
        'total_employees': total_employees,
        'employees_with_tasks': employees_with_tasks,
    }
    
    return render(request, 'tasks/employee_tasks_list.html', context)


@login_required  
def employee_task_detail(request, employee_id):
    """
    Display specific employee's tasks (finished and unfinished) - view only
    """
    employee = get_object_or_404(Employee, pk=employee_id, is_active_employee=True)
    
    # Get all tasks for this employee (both assigned and created)
    assigned_tasks = Task.objects.filter(assigned_to=employee).select_related('project', 'created_by')
    created_tasks = Task.objects.filter(created_by=employee).select_related('project', 'assigned_to')
    
    # Apply filters
    status_filter = request.GET.get('status', '')
    project_filter = request.GET.get('project', '')
    search_query = request.GET.get('search', '')
    
    if status_filter:
        if status_filter == 'finished':
            assigned_tasks = assigned_tasks.filter(status='finished')
            created_tasks = created_tasks.filter(status='finished')
        elif status_filter == 'new':
            assigned_tasks = assigned_tasks.filter(status='new')
            created_tasks = created_tasks.filter(status='new')
    
    if project_filter:
        assigned_tasks = assigned_tasks.filter(project_id=project_filter)
        created_tasks = created_tasks.filter(project_id=project_filter)
    
    if search_query:
        search_q = Q(name__icontains=search_query) | Q(detail__icontains=search_query)
        assigned_tasks = assigned_tasks.filter(search_q)
        created_tasks = created_tasks.filter(search_q)
    
    # Order by date
    assigned_tasks = assigned_tasks.order_by('-created_at')
    created_tasks = created_tasks.order_by('-created_at')
    
    # Get projects for filter
    projects = Project.objects.filter(
        Q(tasks__assigned_to=employee) | Q(tasks__created_by=employee)
    ).distinct().order_by('name')
    
    # Statistics
    stats = {
        'total_assigned': Task.objects.filter(assigned_to=employee).count(),
        'total_created': Task.objects.filter(created_by=employee).count(),
        'finished_assigned': Task.objects.filter(assigned_to=employee, status='finished').count(),
        'finished_created': Task.objects.filter(created_by=employee, status='finished').count(),
        'pending_assigned': Task.objects.filter(assigned_to=employee, status='new').count(),
        'pending_created': Task.objects.filter(created_by=employee, status='new').count(),
    }
    
    context = {
        'title': f'مهام {employee.name}',
        'current_page': 'employee_tasks',
        'employee': employee,
        'assigned_tasks': assigned_tasks,
        'created_tasks': created_tasks,
        'projects': projects,
        'stats': stats,
        'status_filter': status_filter,
        'project_filter': project_filter,
        'search_query': search_query,
        'status_choices': [
            ('', 'جميع المهام'),
            ('new', 'المهام الجديدة'),
            ('finished', 'المهام المكتملة'),
        ]
    }
    
    return render(request, 'tasks/employee_task_detail.html', context)