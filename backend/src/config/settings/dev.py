"""
Настройки для разработки.
Вся env-логика здесь.
"""
from .base import *
import environ

env = environ.Env(
    DEBUG=(bool, True),
    AUTO_MIGRATE=(bool, True),
)

# Читаем .env из корня проекта (на уровень выше backend/)
environ.Env.read_env(BASE_DIR.parent.parent.parent / '.env')

DEBUG = env('DEBUG')
SECRET_KEY = env('SECRET_KEY', default='django-insecure-dev-key-change-me-in-production')

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1', 'backend'])

# Database
DATABASES = {
    'default': env.db(
        'DATABASE_URL',
        default='postgresql://app_user:app_password@db:5432/app_db'
    )
}

# CORS для dev
CORS_ALLOWED_ORIGINS = env.list(
    'CORS_ALLOWED_ORIGINS',
    default=['http://localhost:3000', 'http://127.0.0.1:3000', 'http://localhost:80']
)

# CSRF_TRUSTED_ORIGINS - важно включить все варианты localhost
# Django проверяет точное совпадение Origin заголовка с одним из значений
# Если запрос идет с http://localhost (без порта), а в списке только http://localhost:80, запрос будет отклонен
csrf_trusted_origins_env = env.list('CSRF_TRUSTED_ORIGINS', default=[])
default_csrf_origins = [
    'http://localhost',
    'http://localhost:80',
    'http://localhost:3000',
    'http://127.0.0.1',
    'http://127.0.0.1:80',
    'http://127.0.0.1:3000',
]
if csrf_trusted_origins_env:
    # Объединяем значения из .env с значениями по умолчанию, убираем дубликаты
    CSRF_TRUSTED_ORIGINS = list(dict.fromkeys(csrf_trusted_origins_env + default_csrf_origins))
else:
    CSRF_TRUSTED_ORIGINS = default_csrf_origins

# Logging для dev (консольный вывод с request ID)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} [{request_id}] {module} {message}',
            'style': '{',
        },
        'json': {
            '()': 'apps.core.logging.JSONFormatter',
        },
    },
    'filters': {
        'request_id': {
            '()': 'apps.core.logging.RequestIDFilter',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
            'filters': ['request_id'],
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
        'apps': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Email backend для dev
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Security для dev (более мягкие настройки)
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
