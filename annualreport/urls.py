from django.urls import path
from . import views

app_name = 'annualreport'

urlpatterns = [
    # Main page
    path('', views.index, name='index'),
    
    # CRUD operations
    path('create/', views.create_achievement, name='create'),
    path('<int:pk>/', views.achievement_detail, name='detail'),
    path('<int:pk>/edit/', views.edit_achievement, name='edit'),
    path('<int:pk>/delete/', views.delete_achievement, name='delete'),
    
    # Export
    path('export/', views.export_report, name='export'),
]