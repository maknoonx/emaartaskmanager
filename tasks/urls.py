from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    # Task management URLs
    path('my-tasks/', views.my_tasks, name='my_tasks'),
    path('finished-tasks/', views.finished_tasks, name='finished_tasks'),
    
    # Employee Tasks URLs - New Addition
    path('employee-tasks/', views.employee_tasks_list, name='employee_tasks_list'),
    path('employee-tasks/<int:employee_id>/', views.employee_task_detail, name='employee_task_detail'),
    
    # تأكد من أن هذه الـ URLs صحيحة
    path('tasks/create/', views.create_task, name='create_task'),  # هذا للإضافة
    path('tasks/<int:pk>/', views.task_detail, name='task_detail'),  # هذا للعرض
    path('tasks/<int:pk>/edit/', views.edit_task, name='edit_task'),  # هذا للتعديل
    path('tasks/<int:pk>/delete/', views.delete_task, name='delete_task'),
    path('tasks/<int:pk>/toggle-status/', views.toggle_task_status, name='toggle_task_status'),
    
    # Monthly goals
    path('monthly-goals/', views.monthly_goals_index, name='monthly_goals'),
    path('monthly-goals/create/', views.monthly_goals_create, name='monthly_goals_create'),
    path('monthly-goals/<int:pk>/', views.monthly_goals_detail, name='monthly_goals_detail'),
    path('monthly-goals/<int:pk>/edit/', views.monthly_goals_edit, name='monthly_goals_edit'),
    path('monthly-goals/<int:pk>/delete/', views.monthly_goals_delete, name='monthly_goals_delete'),

    
    # Projects URLs (moved from programs app)
    path('projects/', views.projects, name='projects'),
    path('projects/create/', views.create_project, name='create_project'),
    path('projects/<int:pk>/', views.project_detail, name='project_detail'),
    path('projects/<int:pk>/edit/', views.edit_project, name='edit_project'),
    path('projects/<int:pk>/delete/', views.delete_project, name='delete_project'),
]