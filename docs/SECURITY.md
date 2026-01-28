# Руководство по безопасности

## Обязательные настройки для production

### 1. Секреты

- ✅ **SECRET_KEY**: Минимум 50 символов, уникальный для каждого окружения
- ✅ **POSTGRES_PASSWORD**: Сильный пароль (минимум 16 символов)
- ✅ **SENTRY_DSN**: Настроить для мониторинга ошибок

**Никогда не коммитьте секреты в репозиторий!**

### 2. Django Security Settings

В production все следующие настройки должны быть включены:

```python
DEBUG = False
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

### 3. ALLOWED_HOSTS

Обязательно укажите ваши домены:

```python
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']
```

### 4. CORS и CSRF

Настройте разрешённые origins:

```python
CORS_ALLOWED_ORIGINS = ['https://yourdomain.com']
CSRF_TRUSTED_ORIGINS = ['https://yourdomain.com']
```

### 5. База данных

- Используйте сильные пароли
- Ограничьте доступ к БД (только из backend сети)
- Регулярно делайте бэкапы
- Используйте SSL соединения в production

### 6. Nginx Security Headers

Все security headers настроены в `reverse-proxy/nginx.conf`:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: SAMEORIGIN`
- `Referrer-Policy: strict-origin-when-cross-origin`

### 7. Rate Limiting

Nginx настроен с rate limiting для:
- `/api/v1/auth/login`: 5 запросов в минуту
- Общий API: 100 запросов в минуту

## Рекомендации

### Пароли

- Минимум 12 символов (настроено в валидаторах)
- Используйте сложные пароли
- Рассмотрите использование password managers

### Логирование

- Не логируйте секреты (пароли, токены, API keys)
- Используйте structured logging для production
- Настройте ротацию логов

### Мониторинг

- Настройте Sentry для отслеживания ошибок
- Мониторьте health endpoints
- Настройте алерты на критические ошибки

### Обновления

- Регулярно обновляйте зависимости (особенно security patches)
- Используйте `pip-audit` или `safety` для проверки уязвимостей
- Следите за security advisories Django и PostgreSQL

## Проверка безопасности

### Перед деплоем в production

- [ ] `SECRET_KEY` установлен и уникален
- [ ] `DEBUG = False`
- [ ] `ALLOWED_HOSTS` настроен
- [ ] CORS и CSRF origins настроены
- [ ] HTTPS включен
- [ ] Security headers работают
- [ ] Rate limiting настроен
- [ ] Sentry настроен (опционально, но рекомендуется)
- [ ] Бэкапы БД настроены
- [ ] Логи не содержат секретов

### Регулярные проверки

- Еженедельно: проверка security advisories
- Ежемесячно: обновление зависимостей
- Ежеквартально: security audit

## Инциденты

При обнаружении уязвимости:

1. Немедленно исправьте в production
2. Обновите зависимости
3. Проверьте логи на признаки компрометации
4. При необходимости - ротируйте секреты
5. Документируйте инцидент

## Дополнительные ресурсы

- [Django Security](https://docs.djangoproject.com/en/5.2/topics/security/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Django Security Advisories](https://www.djangoproject.com/weblog/)
