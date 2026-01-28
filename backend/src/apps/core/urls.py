"""
URL patterns for core app.
"""
from django.urls import path
from . import health

app_name = 'core'

urlpatterns = [
    path('health/', health.health_check, name='health'),
    path('readiness/', health.readiness_check, name='readiness'),
]
