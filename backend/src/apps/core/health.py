"""
Health check endpoints для мониторинга.
"""
from django.http import JsonResponse
from django.db import connection
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import never_cache


@require_http_methods(["GET"])
@never_cache
def health_check(request):
    """
    Простая проверка, что приложение работает.
    Не проверяет БД.
    """
    return JsonResponse({"status": "ok"})


@require_http_methods(["GET"])
@never_cache
def readiness_check(request):
    """
    Проверка готовности принимать трафик.
    Проверяет доступность БД.
    """
    try:
        connection.ensure_connection()
        return JsonResponse({"status": "ready"})
    except Exception as e:
        return JsonResponse(
            {"status": "not ready", "error": str(e)},
            status=503
        )
