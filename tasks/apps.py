from django.apps import AppConfig


class TasksConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tasks'
    
    def ready(self):
        """
        Import signals and notification models when the app is ready
        """
        try:
            import tasks.signals
            import tasks.notification_models
        except ImportError:
            pass