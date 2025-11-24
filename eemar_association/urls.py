from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

# Dashboard view import (create this if not exists)
def dashboard_redirect(request):
    """Redirect root URL to dashboard"""
    return redirect('dashboard:dashboard')

urlpatterns = [
    # Admin interface
    path('admin/', admin.site.urls),
    
    # Root redirect to dashboard
    path('', dashboard_redirect, name='home'),
    
    # Dashboard app
    path('dashboard/', include('dashboard.urls')),
    
    # Employee management
    path('employees/', include('employees.urls')),
    
    # Tasks management
    path('tasks/', include('tasks.urls')),
    
    # Programs management
    path('programs/', include('programs.urls')),
    
    # Reports
    path('reports/', include('reports.urls')),

    # annualreport
    path('annual-report/', include('annualreport.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Admin site customization
admin.site.site_header = "جمعية إعمار - لوحة التحكم"
admin.site.site_title = "إدارة جمعية إعمار"
admin.site.index_title = "مرحباً بك في نظام إدارة جمعية إعمار"