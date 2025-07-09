# Updated Reports App URLs (reports/urls.py)
from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.report_dashboard_view, name='index'),
    path('tasks/', views.task_reports_view, name='tasks'),
    path('employees/', views.employee_reports_view, name='employees'),
    path('programs/', views.program_reports_view, name='programs'),
    path('financial/', views.financial_reports_view, name='financial'),
    path('monthly/', views.monthly_report_view, name='monthly'),
    path('monthly/print/', views.monthly_report_print_view, name='monthly_print'),
    path('yearly/', views.yearly_report_view, name='yearly'),
    path('custom/', views.custom_report_view, name='custom'),
    path('export/<str:report_type>/', views.export_report_view, name='export'),
    path('generate/', views.generate_report_view, name='generate'),
]