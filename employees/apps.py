from django.apps import AppConfig

class EmployeesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'employees'
    verbose_name = 'إدارة الموظفين'
    
    def ready(self):
        # Import signals when app is ready
        try:
            import employees.signals
        except ImportError:
            pass