"""
Script to create superuser interactively.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from django.contrib.auth import get_user_model


def create_superuser():
    """Create superuser interactively"""
    User = get_user_model()
    print("Creating superuser...")
    email = input("Email: ")
    
    if User.objects.filter(email=email).exists():
        print(f"User with email {email} already exists!")
        return
    
    password = input("Password: ")
    full_name = input("Full name (optional): ") or ""
    
    user = User.objects.create_superuser(
        email=email,
        password=password,
        full_name=full_name
    )
    
    print(f"Superuser {email} created successfully!")


if __name__ == '__main__':
    create_superuser()
