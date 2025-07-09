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
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
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
    },
}

# ====== CACHING CONFIGURATION ======
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
SITE_URL = 'http://localhost:8000'  # Change in production
SITE_NAME = 'نظام إدارة جمعية إعمار'

# ====== EMAIL RATE LIMITING ======
EMAIL_RATE_LIMIT = {
    'MAX_EMAILS_PER_HOUR': 50,
    'MAX_EMAILS_PER_DAY': 200,
}

# ====== NOTIFICATION SETTINGS ======
NOTIFICATION_SETTINGS = {
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
}

# ====== EMAIL TEMPLATE SETTINGS ======
EMAIL_TEMPLATE_SETTINGS = {
    'BASE_TEMPLATE': 'emails/base_email.html',
    'LOGO_URL': 'https://your-domain.com/static/img/logo.png',
    'COMPANY_NAME': 'جمعية إعمار',
    'COMPANY_ADDRESS': 'المملكة العربية السعودية',
    'SUPPORT_EMAIL': 'support@eemar.org',
    'SUPPORT_PHONE': '+966-XXX-XXXX',
}