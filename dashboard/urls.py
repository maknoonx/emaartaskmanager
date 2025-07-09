from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Main dashboard
    path('', views.dashboard_view, name='dashboard'),
    
    # User profile and settings
    path('profile/', views.profile_view, name='profile'),
    path('settings/', views.settings_view, name='settings'),
    
    # AJAX endpoints
    path('api/notifications/', views.get_notifications_ajax, name='notifications_ajax'),
]