# Настройка Celery для фоновых задач

Этот документ описывает, как добавить поддержку Celery в проект для выполнения фоновых и периодических задач.

## Когда нужен Celery?

- Отправка email/уведомлений в фоне
- Обработка больших файлов
- Экспорт/импорт данных
- Периодические задачи (отчеты, очистка и т.д.)
- Любые долгие операции, которые не должны блокировать HTTP-запрос

## Установка

### 1. Установите зависимости

```bash
pip install -r requirements/celery.txt
```

Или добавьте в `requirements/base.txt`:
```
celery>=5.3,<6.0
redis>=5.0,<6.0
```

### 2. Раскомментируйте Redis в docker-compose.yml

```yaml
# docker/docker-compose.yml
services:
  redis:
    image: redis:7-alpine
    container_name: django_base_redis
    networks:
      - backend_net
    expose:
      - 6379
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

volumes:
  redis_data:
```

### 3. Добавьте конфигурацию Celery

**Создайте файл `backend/src/config/celery.py`:**

```python
"""
Celery configuration for Django project.
"""
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

app = Celery('config')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
```

**Обновите `backend/src/config/__init__.py`:**

```python
"""
Django config package.
"""
from .celery import app as celery_app

__all__ = ('celery_app',)
```

### 4. Добавьте настройки Celery в settings

**В `backend/src/config/settings/base.py` или `dev.py`:**

```python
# Celery Configuration
CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='redis://redis:6379/0')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default='redis://redis:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

# Периодические задачи (раскомментируйте при необходимости)
# CELERY_BEAT_SCHEDULE = {
#     'example-task': {
#         'task': 'apps.core.tasks.example_task',
#         'schedule': 3600.0,  # каждый час
#     },
# }
```

### 5. Добавьте переменные окружения в .env

```env
# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

## Создание задач

**Пример задачи в `backend/src/apps/core/tasks.py`:**

```python
from celery import shared_task
import logging

logger = logging.getLogger(__name__)

@shared_task
def example_task(param1, param2):
    """Пример фоновой задачи."""
    logger.info(f'Executing example_task with {param1}, {param2}')
    # Ваша логика здесь
    return {'status': 'completed'}

@shared_task
def send_email_task(to_email, subject, body):
    """Отправка email в фоне."""
    from django.core.mail import send_mail
    send_mail(subject, body, None, [to_email])
    return {'sent_to': to_email}
```

**Вызов задачи:**

```python
from apps.core.tasks import example_task

# Асинхронный вызов (возвращает AsyncResult)
result = example_task.delay('value1', 'value2')

# Или с дополнительными параметрами
result = example_task.apply_async(
    args=['value1', 'value2'],
    countdown=60,  # выполнить через 60 секунд
)
```

## Запуск

### Локальная разработка

```bash
# Запуск Redis
docker compose -f docker/docker-compose.yml up -d redis

# Запуск Celery Worker (в отдельном терминале)
docker compose -f docker/docker-compose.yml exec backend \
    celery -A config worker -l info

# Запуск Celery Beat для периодических задач (в отдельном терминале)
docker compose -f docker/docker-compose.yml exec backend \
    celery -A config beat -l info --schedule=/tmp/celerybeat-schedule
```

### Production

Для production рекомендуется добавить отдельные сервисы в docker-compose:

```yaml
  celery-worker:
    build:
      context: ../backend
      dockerfile: Dockerfile
    container_name: django_base_celery_worker
    command: celery -A config worker -l info
    env_file:
      - ../.env
    environment:
      DJANGO_SETTINGS_MODULE: config.settings.prod
    networks:
      - backend_net
    depends_on:
      - db
      - redis
    restart: unless-stopped

  celery-beat:
    build:
      context: ../backend
      dockerfile: Dockerfile
    container_name: django_base_celery_beat
    command: celery -A config beat -l info --schedule=/tmp/celerybeat-schedule
    env_file:
      - ../.env
    environment:
      DJANGO_SETTINGS_MODULE: config.settings.prod
    networks:
      - backend_net
    depends_on:
      - db
      - redis
    restart: unless-stopped
```

## Мониторинг

### Flower (веб-интерфейс для Celery)

```bash
pip install flower

# Запуск
celery -A config flower --port=5555
```

Затем откройте http://localhost:5555 в браузере.

## Troubleshooting

### Задачи не выполняются

1. Проверьте, запущен ли Redis: `docker compose ps redis`
2. Проверьте, запущен ли Worker: `docker compose exec backend ps aux | grep celery`
3. Проверьте логи Worker: `docker compose logs celery-worker`

### Ошибка подключения к Redis

Убедитесь, что:
- Redis сервис запущен
- `CELERY_BROKER_URL` указывает на правильный хост (`redis` в Docker сети)
- Сети Docker настроены корректно

### Периодические задачи не запускаются

Убедитесь, что Celery Beat запущен. Beat только ставит задачи в очередь, Worker их выполняет.
