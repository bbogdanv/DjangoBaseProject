"""
Настройки для тестирования.
"""

import os

from .base import *

# SECRET_KEY для тестов (из env в CI, иначе дефолт)
SECRET_KEY = os.environ.get("SECRET_KEY", "test-secret-key-for-pytest")

# Используем SQLite для тестов (быстрее)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Ускоряем тесты
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Отключаем миграции в тестах (опционально)
# Можно включить, если нужны реальные миграции
# USE_TZ = False

# Логирование для тестов (минимальное)
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.NullHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
}
