# Troubleshooting Guide

Документ описывает проблемы, с которыми можно столкнуться при запуске системы, и их решения.

## Проблемы при первом запуске

### 1. Docker Compose не видит переменные из .env

**Симптомы:**
```
time="..." level=warning msg="The \"POSTGRES_PASSWORD\" variable is not set. Defaulting to a blank string."
time="..." level=warning msg="The \"SECRET_KEY\" variable is not set. Defaulting to a blank string."
```

**Причина:**
Docker Compose по умолчанию ищет `.env` файл в той же директории, где находится `docker-compose.yml`. В нашем случае:
- `docker-compose.yml` находится в `docker/`
- `.env` находится в корне проекта

**Неудачные попытки решения:**
1. ❌ Добавление `env_file: - ../.env` в docker-compose.yml (частично помогло, но не для всех команд)
2. ❌ Использование переменных через `${VAR}` без явного указания `--env-file`

**Решение:**
✅ Добавить `--env-file .env` во все команды docker compose в Makefile:

```makefile
build:
	docker compose -f docker/docker-compose.yml --env-file .env build

up:
	docker compose -f docker/docker-compose.yml --env-file .env up -d

migrate:
	docker compose -f docker/docker-compose.yml --env-file .env exec backend python manage.py migrate
```

**Также добавлено:**
- `env_file: - ../.env` в docker-compose.yml для всех сервисов (`db`, `backend`, `reverse-proxy`)

---

### 2. ModuleNotFoundError: No module named 'config'

**Симптомы:**
```
django_base_backend  | ModuleNotFoundError: No module named 'config'
django_base_backend  | Waiting for database...
django_base_backend  | Traceback (most recent call last):
```

**Причина:**
Скрипт `wait_for_db.py` запускается из `/app/scripts/`, но модуль `config` находится в `/app/src/config/`. Python не может найти модуль, потому что `/app/src` не в `PYTHONPATH`.

**Неудачные попытки решения:**
1. ❌ Изменение `working_dir` в docker-compose.dev.yml
2. ❌ Добавление `PYTHONPATH` в environment переменные docker-compose
3. ❌ Изменение entrypoint в docker-compose.dev.yml (не переопределялся полностью)

**Решение:**
✅ Исправить `wait_for_db.py` - добавить `/app/src` в `sys.path` перед импортом Django:

```python
import sys
import os

# Устанавливаем PYTHONPATH перед импортом Django
if '/app/src' not in sys.path:
    sys.path.insert(0, '/app/src')

import django
```

**Файл:** `backend/scripts/wait_for_db.py`

---

### 3. ValueError: Dependency on app with no migrations: users

**Симптомы:**
```
ValueError: Dependency on app with no migrations: users
```

**Причина:**
Приложение `users` использует кастомную модель `User`, но миграции для него не были созданы. Django пытается применить миграции, но не может найти миграции для `users`.

**Решение:**
✅ Создать миграции для всех приложений:

```bash
docker compose -f docker/docker-compose.yml --env-file .env exec backend python manage.py makemigrations
docker compose -f docker/docker-compose.yml --env-file .env exec backend python manage.py migrate
```

**Также исправлено:**
✅ Улучшен `entrypoint.sh` для автоматического создания миграций при ошибке:

```bash
if [ "$AUTO_MIGRATE" = "true" ]; then
    echo "Running migrations..."
    python manage.py migrate --noinput || {
        echo "Migration failed, trying to create migrations first..."
        python manage.py makemigrations --noinput || true
        python manage.py migrate --noinput || true
    }
fi
```

---

### 4. IndexError: list index out of range в entrypoint.sh

**Симптомы:**
```
IndexError: list index out of range
```

**Причина:**
В `entrypoint.sh` была попытка проверить значение `AUTO_MIGRATE` через индексацию массива, что вызывало ошибку.

**Решение:**
✅ Исправлена логика проверки `AUTO_MIGRATE` в `entrypoint.sh` (см. решение проблемы #3).

---

### 5. Backend контейнер постоянно перезапускается (Restarting)

**Симптомы:**
```
NAME                          STATUS
django_base_backend           Restarting (1) 10 seconds ago
```

**Причина:**
Комбинация проблем:
1. Docker Compose не читал `.env` → переменные были пустыми
2. `wait_for_db.py` не мог найти модуль `config`
3. Миграции не могли примениться из-за отсутствия миграций для `users`

**Решение:**
✅ Комплексное решение всех вышеперечисленных проблем:
1. Исправлен `wait_for_db.py` (добавлен PYTHONPATH)
2. Исправлен `entrypoint.sh` (обработка ошибок миграций)
3. Обновлен Makefile (добавлен `--env-file .env`)
4. Созданы миграции для всех приложений

---

### 6. Health endpoint возвращает 502 Bad Gateway

**Симптомы:**
```html
<html>
<head><title>502 Bad Gateway</title></head>
<body>
<center><h1>502 Bad Gateway</h1></center>
</body>
</html>
```

**Причина:**
Backend контейнер не запускался (перезапускался), поэтому Nginx не мог подключиться к backend.

**Решение:**
✅ Решено автоматически после исправления проблем с backend (см. проблему #5).

---

## Проблемы с подключением к БД

### 7. Database is uninitialized and superuser password is not specified

**Симптомы:**
```
Error: Database is uninitialized and superuser password is not specified.
You must specify POSTGRES_PASSWORD to a non-empty value for the superuser.
```

**Причина:**
Docker Compose не читал переменную `POSTGRES_PASSWORD` из `.env` файла.

**Решение:**
✅ См. проблему #1 - добавление `--env-file .env` в команды docker compose.

---

## Проблемы с dev режимом

### 8. Entrypoint не переопределяется в docker-compose.dev.yml

**Симптомы:**
В dev режиме все еще используется production entrypoint (`/app/scripts/entrypoint.sh`), который запускает Gunicorn вместо Django runserver.

**Причина:**
В docker-compose при использовании нескольких файлов (`-f docker-compose.yml -f docker-compose.dev.yml`) entrypoint из базового файла не переопределяется полностью, если не указать явно.

**Неудачные попытки решения:**
1. ❌ Только изменение `command` в docker-compose.dev.yml
2. ❌ Добавление `working_dir` без изменения entrypoint

**Решение:**
✅ Явно переопределить `entrypoint` в `docker-compose.dev.yml`:

```yaml
services:
  backend:
    entrypoint: ["/bin/bash", "-c"]
    command: >
      cd /app/src &&
      export PYTHONPATH=/app/src &&
      python /app/scripts/wait_for_db.py &&
      if [ "$$AUTO_MIGRATE" = "true" ]; then
        python manage.py migrate --noinput;
      fi &&
      python manage.py collectstatic --noinput &&
      python manage.py runserver 0.0.0.0:8000
```

**Примечание:** В текущей версии используется production режим (Gunicorn), который работает стабильно. Dev режим можно настроить позже при необходимости.

---

## Проблемы с созданием суперпользователя

### 9. Скрипт create_superuser.py не найден

**Симптомы:**
```
python: can't open file '/app/src/scripts/create_superuser.py': [Errno 2] No such file or directory
```

**Причина:**
Скрипт находится в `/app/scripts/`, а не в `/app/src/scripts/`.

**Решение:**
✅ Использовать правильный путь:

```bash
docker compose -f docker/docker-compose.yml --env-file .env exec backend python /app/scripts/create_superuser.py
```

Или использовать стандартную команду Django:

```bash
make superuser
# или
docker compose -f docker/docker-compose.yml --env-file .env exec backend python manage.py createsuperuser
```

---

## Проблемы со статическими файлами

### 10. Статические файлы не загружаются (404 Not Found), Django Admin выглядит без стилей

**Симптомы:**
- Django Admin панель отображается без стилей (CSS не загружается)
- В браузере видны ошибки 404 для файлов типа `/static/admin/css/base.css`
- Интерфейс выглядит "голым" - только HTML без оформления

**Причина:**
1. Изначально Nginx был настроен на обслуживание статических файлов из volume (`/var/www/static/`), но:
   - Volume не был правильно смонтирован между backend и nginx
   - При попытке смонтировать volume возникли проблемы с правами доступа (PermissionError)
2. WhiteNoise был настроен в Django, но Nginx перехватывал запросы к `/static/` до того, как они доходили до Django

**Неудачные попытки решения:**
1. ❌ **Попытка 1:** Добавить `static_volume:/app/staticfiles` в backend и `static_volume:/var/www/static:ro` в nginx
   - **Результат:** `PermissionError: [Errno 13] Permission denied: '/app/staticfiles/admin'`
   - **Причина:** Volume создавался с правами root, а приложение запускается от пользователя `appuser`
   - **Логи:** 
     ```
     PermissionError: [Errno 13] Permission denied: '/app/staticfiles/admin'
     ```
2. ❌ **Попытка 2:** Изменить права доступа к volume через `chown` в entrypoint
   - **Результат:** Не помогло, так как volume монтируется после запуска entrypoint
3. ❌ **Попытка 3:** Использовать `STATICFILES_DIRS` с несуществующей директорией
   - **Результат:** Предупреждение `staticfiles.W004` при каждом `collectstatic`
   - **Причина:** Директория `/app/static` не существует и не нужна

**Решение:**
✅ **Использовать WhiteNoise для обслуживания статических файлов через Django:**

1. **Обновить Nginx конфигурацию** - изменить `location /static/` для проксирования к backend вместо чтения из volume:
   ```nginx
   # Было:
   location /static/ {
       alias /var/www/static/;
       expires 1y;
       add_header Cache-Control "public, immutable";
       access_log off;
   }
   
   # Стало:
   location /static/ {
       proxy_pass http://backend;
       proxy_http_version 1.1;
       expires 1y;
       add_header Cache-Control "public, immutable";
       access_log off;
   }
   ```

2. **Убрать volume mount для статических файлов** из `docker-compose.yml`:
   ```yaml
   # Убрано из backend:
   # - static_volume:/app/staticfiles
   
   # Убрано из nginx:
   # - static_volume:/var/www/static:ro
   ```

3. **Убрать неиспользуемую настройку** `STATICFILES_DIRS` из `settings/base.py`:
   ```python
   # Было:
   STATICFILES_DIRS = [BASE_DIR / 'static']
   
   # Стало:
   # STATICFILES_DIRS не используется - все статические файлы собираются в STATIC_ROOT
   ```

4. **Убедиться, что WhiteNoise правильно настроен** (уже было настроено):
   ```python
   # settings/base.py
   MIDDLEWARE = [
       'django.middleware.security.SecurityMiddleware',
       'whitenoise.middleware.WhiteNoiseMiddleware',  # Должен быть сразу после SecurityMiddleware
       # ...
   ]
   
   STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
   ```

5. **Собрать статические файлы:**
   ```bash
   docker compose -f docker/docker-compose.yml --env-file .env exec backend python manage.py collectstatic --noinput
   ```

**Проверка решения:**
```bash
# Проверить доступность CSS файла
curl -I http://localhost/static/admin/css/base.css
# Должен вернуть: HTTP/1.1 200 OK

# Проверить содержимое
curl http://localhost/static/admin/css/base.css | head -10
# Должен вернуть CSS код
```

**Файлы изменены:**
- `reverse-proxy/nginx.conf` - изменен `location /static/`
- `docker/docker-compose.yml` - убран `static_volume` mount
- `backend/src/config/settings/base.py` - убрана настройка `STATICFILES_DIRS`, исправлен `STATIC_URL`

**Ссылки на документацию:**
- [Django: Managing static files](https://docs.djangoproject.com/en/5.2/howto/static-files/)
- [WhiteNoise documentation](http://whitenoise.evans.io/en/stable/)

**Примечание:** WhiteNoise - это рекомендуемый способ обслуживания статических файлов в Django приложениях, развернутых в контейнерах. Он автоматически сжимает файлы, добавляет правильные заголовки кэширования и работает быстрее, чем обслуживание через Nginx напрямую.

---

## Общие рекомендации

### Проверка статуса

```bash
# Проверить статус всех контейнеров
docker compose -f docker/docker-compose.yml --env-file .env ps

# Проверить логи конкретного сервиса
docker compose -f docker/docker-compose.yml --env-file .env logs backend
docker compose -f docker/docker-compose.yml --env-file .env logs db
```

### Перезапуск сервисов

```bash
# Остановить все
make down

# Запустить заново
make up

# Или с пересборкой
make build
make up
```

### Проверка переменных окружения

```bash
# Проверить, что Docker Compose видит переменные
docker compose -f docker/docker-compose.yml --env-file .env config | grep POSTGRES_PASSWORD
```

### Проверка подключения к БД

```bash
# Проверить подключение к локальной БД
docker compose -f docker/docker-compose.yml --env-file .env exec db psql -U app_user -d app_db -c "SELECT 1;"
```

---

## Чеклист при проблемах

1. ✅ Проверьте, что `.env` файл существует и заполнен
2. ✅ Убедитесь, что используете `--env-file .env` в командах docker compose
3. ✅ Проверьте логи: `docker compose -f docker/docker-compose.yml --env-file .env logs backend`
4. ✅ Проверьте статус контейнеров: `docker compose -f docker/docker-compose.yml --env-file .env ps`
5. ✅ Убедитесь, что миграции применены: `make migrate`
6. ✅ Пересоберите образы после изменений в коде: `make build`
7. ✅ Проверьте health endpoint: `curl http://localhost/health/`

---

## Полезные команды для отладки

```bash
# Войти в контейнер backend
docker compose -f docker/docker-compose.yml --env-file .env exec backend bash

# Django shell
make shell

# Проверить настройки Django
docker compose -f docker/docker-compose.yml --env-file .env exec backend python manage.py diffsettings

# Проверить подключение к БД
docker compose -f docker/docker-compose.yml --env-file .env exec backend python manage.py dbshell

# Показать все миграции
docker compose -f docker/docker-compose.yml --env-file .env exec backend python manage.py showmigrations
```

---

## Известные предупреждения (не критичные)

### WARNING: staticfiles.W004

```
?: (staticfiles.W004) The directory '/app/static' in the STATICFILES_DIRS setting does not exist.
```

**Статус:** ✅ **Исправлено** (см. проблему #10)

**Причина:** Директория `/app/static` не существует, но была указана в `STATICFILES_DIRS`.

**Решение:** Убрана настройка `STATICFILES_DIRS` из `settings/base.py`, так как она не используется.

---

---

## Проблемы с таймаутами

### 11. 502 Bad Gateway или WORKER TIMEOUT при долгих запросах

**Симптомы:**
- При экспорте данных, генерации отчетов или других долгих операциях возникает ошибка `502 Bad Gateway`
- В логах Gunicorn видно: `[CRITICAL] WORKER TIMEOUT (pid:XXX)`
- Операция прерывается через ~30-60 секунд

**Причина:**
По умолчанию в системе установлены консервативные таймауты:
- Nginx: `proxy_read_timeout` = 60s (по умолчанию)
- Gunicorn: `--timeout` = 120s

Для долгих операций эти значения могут быть недостаточны.

**Решение:**
✅ Увеличены таймауты во всех компонентах:

**1. Nginx (`reverse-proxy/nginx.conf`):**
```nginx
location /api/ {
    # Увеличенные таймауты для долгих запросов
    proxy_connect_timeout 60s;
    proxy_send_timeout 300s;
    proxy_read_timeout 300s;
    # ...
}
```

**2. Gunicorn (`backend/scripts/entrypoint.sh`):**
```bash
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --timeout 300 \  # Увеличен с 120 до 300 секунд
    --access-logfile - \
    --error-logfile -
```

**Результат:**
- Операции до 5 минут теперь выполняются без таймаутов
- Для более долгих операций рекомендуется использовать Celery (см. `docs/CELERY_SETUP.md`)

---

## История изменений

- **2026-01-20**: Обновление
  - Добавлена проблема #11: 502 Bad Gateway при долгих запросах
  - Увеличены таймауты в Nginx (300s) и Gunicorn (300s)
  - Добавлена документация по Celery (`docs/CELERY_SETUP.md`)
  - Добавлен `pytz` в зависимости

- **2026-01-18**: Первая версия документации
  - Задокументированы проблемы с Docker Compose и .env
  - Задокументированы проблемы с модулем config
  - Задокументированы проблемы с миграциями
  - Задокументированы проблемы со статическими файлами
  - Добавлены решения и неудачные попытки

## Проблемы с авторизацией

### 12. Редирект без авторизации после logout

**Симптомы:**
- После выхода из системы (`/admin/logout/`) и перехода на `http://localhost/` происходит редирект на защищенные страницы без запроса авторизации
- Пользователь может получить доступ к защищенным страницам без логина

**Причина:**
1. В браузере остаются cookies от предыдущей сессии (сессия не полностью очищается)
2. Django может кэшировать состояние авторизации
3. Декоратор `@login_required` может не срабатывать корректно в некоторых случаях

**Решение:**
✅ **Усиление настроек сессии в `settings/base.py`:**

```python
SESSION_COOKIE_AGE = 86400  # 24 часа
SESSION_EXPIRE_AT_BROWSER_CLOSE = True  # Сессия истекает при закрытии браузера
LOGIN_URL = '/admin/login/'
```

✅ **Строгая проверка авторизации в views:**
```python
@login_required(login_url='/admin/login/')
def protected_view(request):
    # Строгая проверка авторизации
    if not request.user or not request.user.is_authenticated:
        # Принудительно очищаем сессию если она есть
        if hasattr(request, 'session'):
            request.session.flush()
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path(), login_url='/admin/login/')
    
    return render(request, 'template.html')
```

**Рекомендации для пользователя:**
- Очистить cookies для localhost в браузере (F12 → Application → Cookies → localhost)
- Или использовать режим инкогнито для тестирования
- Или закрыть и открыть браузер заново

**Ссылки на документацию:**
- [Django: Authentication](https://docs.djangoproject.com/en/5.2/topics/auth/)
- [Django: Session framework](https://docs.djangoproject.com/en/5.2/topics/http/sessions/)

---

## Проблемы с REST Framework

### 13. HTTP 404 при вызове API (проблема с версионированием)

**Симптомы:**
- При вызове API endpoint возникает ошибка `HTTP 404`
- В логах или ответе API видна ошибка: `{"detail":"Недопустимая версия в пути URL. Не соответствует ни одному version namespace."}`

**Причина:**
REST Framework был настроен с `NamespaceVersioning`, который требует версию в namespace URL. `NamespaceVersioning` ищет версию в namespace (например, `v1:api`), но если namespace не настроен правильно, запрос отклоняется.

**Неудачные попытки решения:**
1. ❌ Создание middleware для отключения версионирования - не работает, так как REST Framework проверяет версию до middleware
2. ❌ Установка `request.version = None` в views - не работает, проверка происходит до вызова view
3. ❌ Перемещение API под `/api/v1/` с `NamespaceVersioning` - все еще требует версию в namespace

**Решение:**
✅ **Изменение типа версионирования с `NamespaceVersioning` на `URLPathVersioning`:**

```python
# settings/base.py
REST_FRAMEWORK = {
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.URLPathVersioning',
    'ALLOWED_VERSIONS': ['v1'],
    'DEFAULT_VERSION': 'v1',
    # ...
}
```

**Объяснение:**
- `NamespaceVersioning` определяет версию по namespace в URL (например, `v1:api`)
- `URLPathVersioning` определяет версию по пути URL (например, `/api/v1/` → версия `v1`)
- Для случая, когда версия указана в пути URL (`/api/v1/`), `URLPathVersioning` подходит лучше

**Ссылки на документацию:**
- [Django REST Framework: Versioning](https://www.django-rest-framework.org/api-guide/versioning/)
- [Django REST Framework: URLPathVersioning](https://www.django-rest-framework.org/api-guide/versioning/#urlpathversioning)
- [Django REST Framework: NamespaceVersioning](https://www.django-rest-framework.org/api-guide/versioning/#namespaceversioning)

---

### 14. HTTP 403 - CSRF Failed: Origin checking failed

**Симптомы:**
- При POST/PATCH/DELETE запросе возникает ошибка `HTTP 403`
- Сообщение: `CSRF Failed: Origin checking failed - http://localhost does not match any trusted origins.`

**Причина:**
Django проверяет заголовок `Origin` в запросах и требует, чтобы он был в списке `CSRF_TRUSTED_ORIGINS`. Если в настройках указаны только `http://localhost:80` и `http://localhost:3000`, но запрос идет с `http://localhost` (без порта), Django отклоняет запрос.

**Решение:**
✅ **Добавление всех вариантов localhost в `CSRF_TRUSTED_ORIGINS`:**

```python
# settings/dev.py
csrf_trusted_origins_env = env.list('CSRF_TRUSTED_ORIGINS', default=[])
default_csrf_origins = [
    'http://localhost',
    'http://localhost:80',
    'http://localhost:3000',
    'http://127.0.0.1',
    'http://127.0.0.1:80',
    'http://127.0.0.1:3000',
]
if csrf_trusted_origins_env:
    CSRF_TRUSTED_ORIGINS = list(dict.fromkeys(csrf_trusted_origins_env + default_csrf_origins))
else:
    CSRF_TRUSTED_ORIGINS = default_csrf_origins
```

**Важно:** Django проверяет точное совпадение Origin заголовка с одним из значений в `CSRF_TRUSTED_ORIGINS`. Если запрос идет с `http://localhost` (без порта), а в списке только `http://localhost:80`, запрос будет отклонен.

**Ссылки на документацию:**
- [Django: CSRF protection](https://docs.djangoproject.com/en/5.2/ref/csrf/)
- [Django: CSRF_TRUSTED_ORIGINS](https://docs.djangoproject.com/en/5.2/ref/settings/#csrf-trusted-origins)

---

## История изменений

- **2026-01-28**: Обновление
  - Добавлена проблема #12: Редирект без авторизации после logout
  - Добавлена проблема #13: HTTP 404 при вызове API (проблема с версионированием)
  - Добавлена проблема #14: HTTP 403 - CSRF Failed: Origin checking failed
  - Изменен REST Framework на URLPathVersioning
  - Улучшены настройки сессии
  - Улучшены CSRF_TRUSTED_ORIGINS для dev окружения

- **2026-01-28**: Обновление
  - Добавлена проблема #15: Неконсистентный MEDIA_URL
  - Добавлена проблема #16: Permission denied при загрузке файлов в Docker volume
  - Исправлен MEDIA_URL: `/media/` вместо `media/`
  - Добавлено создание media директории в entrypoint.sh

- **2026-01-24**: Рекомендации из других проектов (MCP)
  - Изучены все записи на MCP troubleshooting (Pheme-Source-AdminPanel, SourceAdminPanel, v2dbweb, WebSite-Monitoring, TelegramMonitoringAnalyst, MCP-TROUBLESHOOTING, TgFeedbackBot-v4)
  - Добавлены проблемы #17–#25: TIME_ZONE Kyiv, get_user_model(), JSONField circular reference, pytz.UTC, перезапуск после .env, уникальные имена файлов, static/media в DEBUG, client_max_body_size, фиксированные версии образов
  - В `config/urls.py` добавлено обслуживание static/media в DEBUG для runserver

## Проблемы с файлами

### 15. Неконсистентный MEDIA_URL

**Симптомы:**
- Медиа файлы не загружаются корректно
- URL медиа файлов отображаются без начального слэша

**Причина:**
`MEDIA_URL = 'media/'` без начального слэша несовместимо с форматом `STATIC_URL = '/static/'`.

**Решение:**
✅ **Исправить MEDIA_URL в `settings/base.py`:**

```python
# Было:
MEDIA_URL = 'media/'

# Стало:
MEDIA_URL = '/media/'
```

---

### 16. Permission denied при загрузке файлов в Docker volume

**Симптомы:**
- При попытке загрузить файл возникает ошибка `[Errno 13] Permission denied`
- Директория media не создается автоматически
- Docker volume создается с правами root

**Причина:**
Docker volumes создаются с правами root по умолчанию. Если приложение запускается от обычного пользователя (appuser), оно не может записывать в директорию, принадлежащую root.

**Решение:**
✅ **Добавить создание media директории в `entrypoint.sh`:**

```bash
echo "Setting up media directory..."
# Создаем директорию для медиа файлов, если её нет
MEDIA_DIR="${MEDIA_ROOT:-/app/media}"
mkdir -p "$MEDIA_DIR"
# Устанавливаем правильные права доступа
chmod -R 755 "$MEDIA_DIR" 2>/dev/null || true
```

**Примечание:** Это предотвращает Permission denied ошибки при загрузке файлов в Docker volumes.

---

## Рекомендации из других Django-проектов (MCP troubleshooting)

Ниже — практики из troubleshooting других проектов на Django/Docker, полезные для базовой сборки.

### 17. TIME_ZONE: Europe/Kyiv, не Europe/Kiev

**Источник:** v2dbweb

**Симптомы:** `ValueError: Incorrect timezone setting: Europe/Kiev`

**Причина:** В Django корректное значение — `Europe/Kyiv`, не `Europe/Kiev`.

**Решение:** В настройках использовать:
```python
TIME_ZONE = 'Europe/Kyiv'  # не 'Europe/Kiev'
```
В базовой сборке по умолчанию `TIME_ZONE = 'UTC'` — менять только при необходимости.

---

### 18. get_user_model() только внутри кода, не на уровне модуля

**Источник:** v2dbweb

**Симптомы:** `ImproperlyConfigured: Requested setting AUTH_USER_MODEL, but settings are not configured.`

**Причина:** Вызов `get_user_model()` на уровне модуля до загрузки Django settings (например, в импортах моделей).

**Решение:** Вызывать `get_user_model()` только внутри функций/методов после `django.setup()` или внутри приложения:
```python
from django.contrib.auth import get_user_model

def my_function():
    User = get_user_model()
    # ...
```

---

### 19. JSONField и циклические ссылки

**Источник:** v2dbweb

**Симптомы:** `ValueError: Circular reference detected` при сохранении в `JSONField`.

**Причина:** В словарь для `JSONField` попадают объекты с циклическими ссылками (например, Django-модели или вложенные ссылки).

**Решение:** Перед записью делать «глубокую копию» через JSON:
```python
import json
Model.objects.create(
    search_link=json.loads(json.dumps(data)),  # разрыв циклических ссылок
)
```

---

### 20. pytz.UTC вместо timezone.utc

**Источник:** TelegramMonitoringAnalyst

**Симптомы:** `AttributeError: module 'django.utils.timezone' has no attribute 'utc'` при работе с Celery/расписаниями.

**Причина:** В Django нет `timezone.utc`; для явной работы с UTC нужен `pytz`.

**Решение:** Использовать `pytz.UTC` (в проекте уже есть зависимость `pytz`):
```python
import pytz
next_run = run_datetime.astimezone(pytz.UTC)
```

---

### 21. Полный перезапуск после изменения .env

**Источник:** SourceAdminPanel, TelegramMonitoringAnalyst

**Симптомы:** После правок в `.env` переменные не подхватываются, даже после `docker compose restart backend`.

**Причина:** Docker Compose кэширует переменные окружения при создании контейнера.

**Решение:** Полностью пересоздать контейнер:
```bash
docker compose -f docker/docker-compose.yml --env-file .env down backend
docker compose -f docker/docker-compose.yml --env-file .env up -d backend
# или
make down && make up
```

---

### 22. Уникальные имена файлов при массовой генерации

**Источник:** TelegramMonitoringAnalyst

**Симптомы:** `IntegrityError: duplicate key value violates unique constraint` при создании файлов с именами по шаблону `name_%Y%m%d_%H%M%S`.

**Причина:** Несколько записей создаются в одну секунду — совпадает timestamp в имени.

**Решение:** Добавлять короткий уникальный суффикс (например, от UUID):
```python
import uuid
filename = f"export_{user_id}_{timestamp}_{uuid.uuid4().hex[:6]}.json"
```

---

### 23. Статика и медиа в режиме DEBUG (runserver)

**Источник:** v2dbweb

**Симптомы:** При `runserver` без Nginx статика/медиа по `/static/` и `/media/` не отдаются.

**Причина:** В `urls.py` не подключено обслуживание статики и медиа для DEBUG.

**Решение:** В корневом `urls.py` добавить (если нужен runserver без WhiteNoise для статики):
```python
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # ...
]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```
В базовой сборке статику в dev обслуживает WhiteNoise; этот вариант — запасной для локального runserver.

---

### 24. Ограничение размера тела запроса (413) и загрузки файлов

**Источник:** MCP-TROUBLESHOOTING, Pheme

**Симптомы:** `413 Payload Too Large` при загрузке больших файлов или больших JSON-тел.

**Решение:** В проекте уже задано в Nginx: `client_max_body_size 10M;`. Для больших загрузок увеличить в `reverse-proxy/nginx.conf`:
```nginx
client_max_body_size 50M;  # или нужное значение
```

---

### 25. Docker: образы с фиксированной версией, не latest

**Источник:** TgFeedbackBot-v4

**Рекомендация:** В `docker-compose.yml` и Dockerfile использовать образы с конкретным тегом (например, `postgres:16-alpine`, `nginx:1.28-alpine`), а не `latest`, чтобы сборка была воспроизводимой. В базовой сборке это уже соблюдено.
