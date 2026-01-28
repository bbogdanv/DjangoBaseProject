"""
Custom User model with email as primary identifier.
"""
import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from .managers import UserManager


class User(AbstractUser):
    """
    Кастомная User модель с email как primary identifier.
    
    Username автогенерируется, если не задан явно.
    Это обеспечивает совместимость с Django ecosystem (admin, createsuperuser),
    но email используется для аутентификации.
    """
    email = models.EmailField(
        unique=True,
        blank=False,
        null=False,
        db_index=True,
        verbose_name='Email адрес'
    )
    full_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Полное имя'
    )
    is_email_verified = models.BooleanField(
        default=False,
        verbose_name='Email подтверждён'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )
    
    # Username делаем опциональным, но оставляем для совместимости
    username = models.CharField(
        max_length=150,
        unique=True,
        null=True,
        blank=True,
        db_index=True
    )
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    objects = UserManager()
    
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['username']),
        ]
    
    def __str__(self):
        return self.email
    
    def save(self, *args, **kwargs):
        """Автогенерация username, если не задан"""
        if not self.username:
            # Генерируем уникальный username на основе email или UUID
            if self.email:
                base_username = self.email.split('@')[0]
                # Очищаем от недопустимых символов
                base_username = ''.join(c for c in base_username if c.isalnum() or c in '._-')
                # Ограничиваем длину
                base_username = base_username[:50]
            else:
                base_username = 'user'
            
            # Добавляем UUID для уникальности
            unique_suffix = uuid.uuid4().hex[:12]
            self.username = f"{base_username}_{unique_suffix}"
        
        super().save(*args, **kwargs)
