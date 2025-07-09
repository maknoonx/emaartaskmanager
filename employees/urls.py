
from django.urls import path
from . import views

app_name = 'employees'

urlpatterns = [
    # Authentication URLs - ADD THESE AT THE TOP
    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),
    
    # Existing URLs
    path('', views.index, name='index'),
    path('create/', views.create, name='create'),
    path('<int:pk>/', views.detail, name='detail'),
    path('<int:pk>/edit/', views.edit, name='edit'),
    path('<int:pk>/delete/', views.delete, name='delete'),
    path('<int:pk>/toggle-status/', views.toggle_status, name='toggle_status'),
]
