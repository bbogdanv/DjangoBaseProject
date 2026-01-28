"""
API URLs - минимальный скелет для DRF.
Может быть пустым, если API не используется.
"""

from django.urls import path
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(["GET"])
def api_root(request):
    """API root endpoint"""
    return Response(
        {
            "message": "Django Base Project API",
            "version": "v1",
            "endpoints": {
                "health": "/health/",
                "readiness": "/readiness/",
            },
        }
    )


app_name = "api"

urlpatterns = [
    path("", api_root, name="api-root"),
]
