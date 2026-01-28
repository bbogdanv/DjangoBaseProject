"""
App configuration for API app.
"""
from django.apps import AppConfig


class ApiConfig(AppConfig):
    """Configuration for API app"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.api'
    verbose_name = 'API'
