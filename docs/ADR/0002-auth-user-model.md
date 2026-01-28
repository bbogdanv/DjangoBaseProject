# ADR-0002: Аутентификация и User модель

## Статус

Принято

## Контекст

Необходимо определить подход к аутентификации и модели пользователя для базового шаблона. Требования:
- Email как primary identifier (современный подход)
- Совместимость с Django ecosystem (admin, createsuperuser)
- Гибкость для будущих расширений
- Безопасность по умолчанию

## Решение

### User модель

Использовать **AbstractUser** с кастомизацией:
- `email` как `USERNAME_FIELD` (primary identifier)
- `username` опциональный, автогенерируется если не задан
- Минимальные дополнительные поля: `full_name`, `is_email_verified`, `created_at`, `updated_at`

### Почему AbstractUser, а не AbstractBaseUser

1. **Совместимость с Django ecosystem**:
   - Admin панель работает из коробки
   - `createsuperuser` работает без изменений
   - Все стандартные auth views работают

2. **Меньше кастомизации**:
   - Не нужно реализовывать базовые поля (`is_active`, `is_staff`, `is_superuser`)
   - Меньше кода для поддержки

3. **Гибкость**:
   - Можно добавить дополнительные поля позже
   - Легко расширить функциональность

### Почему email как USERNAME_FIELD

1. **Современный подход**: Email - стандартный идентификатор в современных приложениях
2. **Уникальность**: Email уникален по природе
3. **UX**: Пользователям проще запомнить email, чем username

### Почему username сохранён

1. **Совместимость**: Некоторые части Django ecosystem ожидают username
2. **Автогенерация**: Username генерируется автоматически из email + UUID
3. **Гибкость**: Можно использовать username для legacy систем или специальных случаев

### Аутентификация

- **По умолчанию**: Django sessions (для admin, backoffice)
- **Опционально**: JWT через django-rest-framework-simplejwt (для API)
- Оба подхода могут сосуществовать

## Реализация

### User модель

```python
class User(AbstractUser):
    email = models.EmailField(unique=True, ...)
    USERNAME_FIELD = 'email'
    username = models.CharField(unique=True, null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.username:
            # Автогенерация username
        super().save(*args, **kwargs)
```

### Миграции

Важно: User модель должна быть определена **до первой миграции**, так как это влияет на все последующие миграции.

## Последствия

### Положительные

- ✅ Email-first подход (современный)
- ✅ Совместимость с Django ecosystem
- ✅ Гибкость для расширения
- ✅ Безопасность (email verification готов)

### Отрицательные

- ⚠️ Username всё ещё требуется (но автогенерируется)
- ⚠️ Нужно помнить про автогенерацию при создании пользователей

### Митигация

- Документировать использование email для аутентификации
- В admin панели использовать email как primary field
- Тесты для проверки автогенерации username

## Альтернативы

### Рассмотренные варианты

1. **AbstractBaseUser**:
   - ❌ Требует больше кастомизации
   - ❌ Может сломать совместимость с некоторыми пакетами
   - ✅ Полный контроль над полями

2. **Стандартная User модель Django**:
   - ❌ Username обязателен
   - ❌ Не соответствует современным практикам
   - ✅ Максимальная совместимость

3. **JWT только**:
   - ❌ Не подходит для admin панели
   - ❌ Усложняет разработку
   - ✅ Stateless (но не критично для большинства проектов)

## Ссылки

- [Django Custom User Model](https://docs.djangoproject.com/en/5.2/topics/auth/customizing/#using-a-custom-user-model-when-starting-a-project)
- [AbstractUser vs AbstractBaseUser](https://docs.djangoproject.com/en/5.2/topics/auth/customizing/#extending-django-s-default-user)
