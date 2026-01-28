"""
Wait for database to be ready.
"""
import sys
import time
import os

# Устанавливаем PYTHONPATH перед импортом Django
if '/app/src' not in sys.path:
    sys.path.insert(0, '/app/src')

import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from django.db import connection
from django.core.management import execute_from_command_line


def wait_for_db(max_retries=30, delay=1):
    """Wait for database connection"""
    for i in range(max_retries):
        try:
            connection.ensure_connection()
            print("Database is ready!")
            return True
        except Exception as e:
            if i < max_retries - 1:
                print(f"Waiting for database... ({i+1}/{max_retries})")
                time.sleep(delay)
            else:
                print(f"Database connection failed: {e}")
                return False
    return False


if __name__ == '__main__':
    if not wait_for_db():
        sys.exit(1)
