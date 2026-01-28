#!/bin/bash
set -e

echo "Waiting for database..."
python /app/scripts/wait_for_db.py

echo "Setting up media directory..."
# Создаем директорию для медиа файлов, если её нет
# Получаем путь из переменной окружения или используем значение по умолчанию
MEDIA_DIR="${MEDIA_ROOT:-/app/media}"
mkdir -p "$MEDIA_DIR"
# Устанавливаем правильные права доступа
# В контейнере appuser имеет UID 1000, но мы не можем использовать chown без root
# Поэтому просто убеждаемся, что директория существует и имеет правильные права
chmod -R 755 "$MEDIA_DIR" 2>/dev/null || true

# Миграции только если AUTO_MIGRATE=true
if [ "$AUTO_MIGRATE" = "true" ]; then
    echo "Running migrations..."
    python manage.py migrate --noinput || {
        echo "Migration failed, trying to create migrations first..."
        python manage.py makemigrations --noinput || true
        python manage.py migrate --noinput || true
    }
fi

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting server..."
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --timeout 300 \
    --access-logfile - \
    --error-logfile -
