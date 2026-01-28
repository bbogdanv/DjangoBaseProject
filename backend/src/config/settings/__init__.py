"""
Settings module initialization.
Loads settings based on DJANGO_SETTINGS_MODULE environment variable.
"""
import os

# Определяем, какой settings файл использовать
# По умолчанию - development
settings_module = os.environ.get('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

if settings_module == 'config.settings.dev':
    from .dev import *
elif settings_module == 'config.settings.prod':
    from .prod import *
elif settings_module == 'config.settings.test':
    from .test import *
else:
    from .base import *
