"""
Custom logging formatters and filters.
"""
import json
import logging
import threading
from datetime import datetime


# Thread-local storage для request ID
_thread_local = threading.local()


def get_request_id():
    """Получить request ID из thread-local storage"""
    return getattr(_thread_local, 'request_id', None)


def set_request_id(request_id):
    """Установить request ID в thread-local storage"""
    _thread_local.request_id = request_id


class RequestIDFilter(logging.Filter):
    """
    Logging filter для добавления request_id в каждую запись лога.
    """

    def filter(self, record):
        record.request_id = get_request_id() or 'no-request-id'
        return True


class JSONFormatter(logging.Formatter):
    """
    JSON formatter для structured logging.
    Используется в production для интеграции с log aggregators.
    """

    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }

        # Добавляем request_id, если есть
        request_id = getattr(record, 'request_id', None)
        if request_id:
            log_data['request_id'] = request_id

        # Добавляем exception info, если есть
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        # Добавляем extra fields
        for key, value in record.__dict__.items():
            if key not in [
                'name', 'msg', 'args', 'created', 'filename', 'funcName',
                'levelname', 'levelno', 'lineno', 'module', 'msecs',
                'message', 'pathname', 'process', 'processName', 'relativeCreated',
                'thread', 'threadName', 'exc_info', 'exc_text', 'stack_info',
                'request_id'
            ]:
                log_data[key] = value

        return json.dumps(log_data)
