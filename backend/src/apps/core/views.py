"""
Core views (placeholder for future views).
"""

from django.http import JsonResponse


def index(request):
    """Simple index view"""
    return JsonResponse({"message": "Django Base Project API", "version": "1.0.0"})
