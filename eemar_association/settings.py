import os
from pathlib import Path
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-^hsmory_&c%pbxe6zlxdmfs1nxzi*dw@y_b_0n9cgczvfua5rv')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'

ALLOWED_HOSTS = ['*']

# CSRF settings
CSRF_COOKIE_SECURE = False  # Set to True when using HTTPS
CSRF_COOKIE_HTTPONLY = False  # Must be False for JavaScript access
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_USE_SESSIONS = False
CSRF_COOKIE_NAME = 'csrftoken'

# CSRF settings for Railway deployment
CSRF_TRUSTED_ORIGINS = [
    'https://emaartaskmanager-production.up.railway.app',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'dashboard',
    'tasks',
    'employees', 
    'programs',
    'reports',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'eemar_association.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'eemar_association.wsgi.application'

# Database
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:eovXTltcguBcJJYLMDlnYSmNDPVFQMBK@interchange.proxy.rlwy.net:56078/railway')

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL)
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'ar'
TIME_ZONE = 'Asia/Riyadh'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / "static",
]
STATIC_ROOT = BASE_DIR / 'staticfiles'

# WhiteNoise configuration
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files (User uploaded files)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ====== CUSTOM USER MODEL ======
AUTH_USER_MODEL = 'employees.Employee'

# ====== AUTHENTICATION BACKENDS ======
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

# ====== LOGIN/LOGOUT CONFIGURATION ======
LOGIN_URL = '/employees/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/employees/login/'

# ====== SECURITY SETTINGS ======
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# ====== FILE UPLOAD SETTINGS ======
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
FILE_UPLOAD_PERMISSIONS = 0o644

# ====== SESSION CONFIGURATION ======
SESSION_COOKIE_AGE = 3600 * 24 * 7  # 1 week
SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# ====== CUSTOM SETTINGS FOR EMPLOYEE MANAGEMENT ======
DEFAULT_EMPLOYEE_PASSWORD = '123456'
EMPLOYEE_NUMBER_PREFIX = 'EMP'
ALLOWED_PROFILE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif']
MAX_PROFILE_PICTURE_SIZE = 5 * 1024 * 1024  # 5MB

EMPLOYEE_SECTIONS = {
    'hr': 'الموارد البشرية',
    'finance': 'المالية',
    'projects': 'المشاريع',
    'programs': 'البرامج',
    'it': 'تقنية المعلومات',
    'admin': 'الإدارة العامة',
    'field': 'العمل الميداني',
    'media': 'الإعلام والتسويق',
    'legal': 'الشؤون القانونية',
    'planning': 'التخطيط والمتابعة',
}

# ====== EMAIL SETTINGS ======
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'emaar2023@gmail.com'
EMAIL_HOST_PASSWORD = 'jofo ffrs siry bfeb'
DEFAULT_FROM_EMAIL = 'جمعية إعمار <emaar2023@gmail.com>'

# ====== CELERY CONFIGURATION ======
# Redis URL for Celery (you can use Railway's Redis or local Redis)
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

# Celery Configuration
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = True

# Celery Task Settings
CELERY_TASK_ALWAYS_EAGER = False  # Set to True for development without Redis
CELERY_TASK_EAGER_PROPAGATES = False
CELERY_TASK_IGNORE_RESULT = False
CELERY_TASK_STORE_EAGER_RESULT = True

# Celery Beat Schedule Settings
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# Use Celery for emails in production
USE_CELERY_FOR_EMAILS = os.environ.get('USE_CELERY_FOR_EMAILS', 'False').lower() == 'true'

# ====== LOGGING CONFIGURATION ======
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
        'notification': {
            'format': '[NOTIFICATION] {asctime} {levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'notification_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'notifications.log',
            'formatter': 'notification',
        },
        'celery_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'celery.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'notifications': {
            'handlers': ['notification_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'celery': {
            'handlers': ['celery_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'celery.task': {
            'handlers': ['celery_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Create logs directory if it doesn't exist
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

# ====== CACHING CONFIGURATION ======
# Use Redis for caching if available, otherwise use local memory
if REDIS_URL and not DEBUG:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': REDIS_URL,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            },
            'KEY_PREFIX': 'eemar_cache',
            'TIMEOUT': 300,  # 5 minutes
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
            'TIMEOUT': 300,  # 5 minutes
            'OPTIONS': {
                'MAX_ENTRIES': 1000,
            }
        }
    }

# ====== PAGINATION SETTINGS ======
DEFAULT_PAGINATION_SIZE = 10
MAX_PAGINATION_SIZE = 100

# ====== SITE CONFIGURATION ======
SITE_URL = os.environ.get('SITE_URL', 'http://localhost:8000')
SITE_NAME = 'نظام إدارة جمعية إعمار'

# ====== EMAIL RATE LIMITING ======
EMAIL_RATE_LIMIT = {
    'MAX_EMAILS_PER_HOUR': 50,
    'MAX_EMAILS_PER_DAY': 200,
}

# ====== ENHANCED NOTIFICATION SETTINGS ======
NOTIFICATION_SETTINGS = {
    'SITE_NAME': SITE_NAME,
    'SITE_URL': SITE_URL,
    'SUPPORT_EMAIL': 'emaar2023@gmail.com',
    'ENABLE_EMAIL_NOTIFICATIONS': True,
    'MAX_DAILY_REMINDERS_PER_TASK': 3,
    'REMINDER_INTERVAL_HOURS': 4,
    
    # Task notifications
    'TASK_ASSIGNED': {
        'enabled': True,
        'email': True,
        'subject_template': 'تم تكليفك بمهمة جديدة - {task_name}',
    },
    'TASK_COMPLETED': {
        'enabled': True,
        'email': True,
        'subject_template': 'تم إنجاز المهمة - {task_name}',
    },
    'TASK_OVERDUE': {
        'enabled': True,
        'email': True,
        'subject_template': 'تنبيه: مهمة متأخرة - {task_name}',
    },
    
    # Deadline reminders
    'TASK_DUE_IN_3_DAYS': {
        'enabled': True,
        'email': True,
        'subject_template': 'تذكير: تنتهي مهمتك بعد 3 أيام - {task_name}',
    },
    'TASK_DUE_TOMORROW': {
        'enabled': True,
        'email': True,
        'subject_template': '⚠️ تنبيه: تنتهي مهمتك غداً - {task_name}',
    },
    'TASK_DUE_TODAY': {
        'enabled': True,
        'email': True,
        'subject_template': '🚨 عاجل جداً: مهمتك تنتهي اليوم - {task_name}',
    },
    
    # High priority reminders
    'HIGH_PRIORITY_REMINDER': {
        'enabled': True,
        'email': True,
        'subject_template': '🔥 عاجل - مهمة عالية الأولوية: {task_name}',
    },
    
    # Daily digest
    'DAILY_DIGEST': {
        'enabled': True,
        'email': True,
        'subject_template': 'الملخص اليومي للمهام - {date}',
    },
}

# ====== DEADLINE REMINDER SETTINGS ======
DEADLINE_REMINDER_SETTINGS = {
    'ENABLED': True,
    'REMINDER_DAYS': [3, 1, 0],  # Days before due date to send reminders
    'MAX_REMINDERS_PER_DAY': 3,
    'REMINDER_INTERVAL_HOURS': 4,
    'WEEKEND_REMINDERS': False,  # Send reminders on weekends
    'HIGH_PRIORITY_EXTRA_REMINDERS': True,
    'DEFAULT_REMINDER_TIME': '09:00',  # Default time to send reminders
}

# ====== EMAIL TEMPLATE SETTINGS ======
EMAIL_TEMPLATE_SETTINGS = {
    'BASE_TEMPLATE': 'emails/base_email.html',
    'LOGO_URL': f'{SITE_URL}/static/img/logo.png',
    'COMPANY_NAME': 'جمعية إعمار',
    'COMPANY_ADDRESS': 'المملكة العربية السعودية',
    'SUPPORT_EMAIL': 'emaar2023@gmail.com',
    'SUPPORT_PHONE': '+966-XXX-XXXX',
    'PRIMARY_COLOR': '#0066cc',
    'SECONDARY_COLOR': '#f8f9fa',
    'SUCCESS_COLOR': '#28a745',
    'WARNING_COLOR': '#ffc107',
    'DANGER_COLOR': '#dc3545',
    'INFO_COLOR': '#17a2b8',
}

# ====== TASK MANAGEMENT SETTINGS ======
TASK_SETTINGS = {
    'DEFAULT_STATUS': 'new',
    'STATUS_CHOICES': [
        ('new', 'جديدة'),
        ('in_progress', 'قيد التنفيذ'),
        ('finished', 'مكتملة'),
        ('cancelled', 'ملغية'),
    ],
    'PRIORITY_CHOICES': [
        ('low', 'منخفضة'),
        ('medium', 'متوسطة'),
        ('high', 'عالية'),
        ('urgent', 'عاجل'),
    ],
    'AUTO_ASSIGN_NOTIFICATIONS': True,
    'AUTO_COMPLETION_NOTIFICATIONS': True,
    'OVERDUE_CHECK_ENABLED': True,
}

# ====== DEVELOPMENT SETTINGS ======
if DEBUG:
    # Development-specific settings
    CELERY_TASK_ALWAYS_EAGER = True  # Execute tasks synchronously in development
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # Print emails to console
    
    # Override notification settings for development
    NOTIFICATION_SETTINGS['ENABLE_EMAIL_NOTIFICATIONS'] = True
    DEADLINE_REMINDER_SETTINGS['ENABLED'] = True

# ====== PRODUCTION SETTINGS ======
if not DEBUG:
    # Production-specific settings
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    
    # Use real email backend in production
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    
    # Enable Celery for background tasks
    USE_CELERY_FOR_EMAILS = True
    CELERY_TASK_ALWAYS_EAGER = False

# ====== CUSTOM MIDDLEWARE SETTINGS ======
CUSTOM_MIDDLEWARE_SETTINGS = {
    'TASK_NOTIFICATION_MIDDLEWARE': True,
    'DEADLINE_TRACKING_MIDDLEWARE': True,
    'EMAIL_RATE_LIMITING_MIDDLEWARE': True,
}

# ====== API SETTINGS (if needed) ======
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': DEFAULT_PAGINATION_SIZE,
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
} if 'rest_framework' in INSTALLED_APPS else {}

# ====== BACKUP SETTINGS ======
BACKUP_SETTINGS = {
    'NOTIFICATION_LOGS_RETENTION_DAYS': 90,
    'TASK_REMINDER_TRACKER_RETENTION_DAYS': 30,
    'EMAIL_LOG_RETENTION_DAYS': 60,
    'AUTO_CLEANUP_ENABLED': True,
}

# ====== MONITORING SETTINGS ======
MONITORING_SETTINGS = {
    'EMAIL_QUEUE_MONITORING': True,
    'CELERY_HEALTH_CHECK': True,
    'NOTIFICATION_STATISTICS': True,
    'DAILY_REPORTS': True,
    'ALERT_THRESHOLDS': {
        'FAILED_NOTIFICATIONS_PER_HOUR': 10,
        'QUEUE_SIZE_WARNING': 100,
        'RESPONSE_TIME_WARNING': 30,  # seconds
    },
}

# Make sure the settings are available in templates
def get_notification_settings():
    return NOTIFICATION_SETTINGS

def get_deadline_reminder_settings():
    return DEADLINE_REMINDER_SETTINGS