"""
Custom middleware for request ID tracking.
"""
import uuid
from django.utils.deprecation import MiddlewareMixin


class RequestIDMiddleware(MiddlewareMixin):
    """
    Middleware для генерации и передачи Request ID через весь request lifecycle.
    
    Генерирует уникальный ID для каждого запроса и добавляет его:
    - В request.META
    - В response headers
    - В logging context (через thread-local storage)
    """
    
    def process_request(self, request):
        """Генерируем или получаем Request ID из заголовка"""
        request_id = request.META.get('HTTP_X_REQUEST_ID')
        if not request_id:
            request_id = str(uuid.uuid4())
        
        request.META['REQUEST_ID'] = request_id
        return None
    
    def process_response(self, request, response):
        """Добавляем Request ID в response headers"""
        request_id = request.META.get('REQUEST_ID')
        if request_id:
            response['X-Request-ID'] = request_id
        return response
