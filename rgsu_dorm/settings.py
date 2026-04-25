"""
Django settings for rgsu_dorm project.
Информационная система оптимизации заселения в общежития РГСУ.
Стек: Django 4.2/5.x, PostgreSQL 16, Celery + Redis, Bootstrap 5.
Соответствует требованиям п. 2.1–2.3 диплома.
"""
import os
from pathlib import Path
import dj_database_url  # <-- ДОБАВЛЕНО: для гибкого подключения к БД
from dotenv import load_dotenv  # <-- ДОБАВЛЕНО: для загрузки .env локально

# Загружаем переменные из .env файла (только для локальной разработки)
load_dotenv()

# Базовый путь к корню проекта
BASE_DIR = Path(__file__).resolve().parent.parent

# Ключ шифрования. В продакшене берётся из переменной окружения!
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-replace-this-key-in-production-7f8g9h0j1k2l3m4n5o6p')

# Режим отладки. False для сервера, управляется переменной окружения
DEBUG = os.getenv('DEBUG', 'True') == 'True'

# Разрешённые хосты. В продакшене: *.onrender.com, ваш-домен
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '127.0.0.1,localhost').split(',')

# -------------------------------------------------------------------
# ПРИЛОЖЕНИЯ
# -------------------------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Планировщик фоновых задач
    'django_celery_beat',

    # Модули проекта
    'users',         # Ролевая модель, профили, авторизация
    'dorms',         # Справочники корпусов и комнат
    'applications',  # Заявки, документы, рейтинги, договоры
    'analytics',     # Отчётность и дашборды
]

# -------------------------------------------------------------------
# ПРОМЕЖУТОЧНОЕ ПО (MIDDLEWARE)
# -------------------------------------------------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # <-- ДОБАВЛЕНО: для раздачи статики на Render
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'rgsu_dorm.urls'
WSGI_APPLICATION = 'rgsu_dorm.wsgi.application'

# -------------------------------------------------------------------
# ШАБЛОНЫ
# -------------------------------------------------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# -------------------------------------------------------------------
# БАЗА ДАННЫХ (PostgreSQL 16)
# -------------------------------------------------------------------
# Гибкая конфигурация: использует DATABASE_URL от Render или локальные настройки
DATABASES = {
    'default': dj_database_url.config(
        # Если DATABASE_URL не задан (локально), используем настройки по умолчанию
        default='postgresql://rgsu_dorm_user:secure_password_123@127.0.0.1:5432/rgsu_dorm_db',
        conn_max_age=600,  # keep connections alive for 10 minutes
        conn_health_checks=True,  # check connection health before use
    )
}

# -------------------------------------------------------------------
# ВАЛИДАЦИЯ ПАРОЛЕЙ
# -------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# -------------------------------------------------------------------
# ИНТЕРНАЦИОНАЛИЗАЦИЯ
# -------------------------------------------------------------------
LANGUAGE_CODE = 'ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

# -------------------------------------------------------------------
# СТАТИКА И МЕДИАФАЙЛЫ (настроено для Render.com)
# -------------------------------------------------------------------
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'  # сюда соберётся вся статика через collectstatic
STATICFILES_DIRS = [BASE_DIR / 'static']  # исходные файлы статики при разработке

# Whitenoise для раздачи статики без Nginx (идеально для Render)
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# -------------------------------------------------------------------
# АВТОРИЗАЦИЯ И РОЛЕВАЯ МОДЕЛЬ (п. 1.1 диплома)
# -------------------------------------------------------------------
AUTH_USER_MODEL = 'users.User'  # Обязательно до первой миграции!
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'applications:status'
LOGOUT_REDIRECT_URL = 'login'

# -------------------------------------------------------------------
# ФОНОВЫЕ ЗАДАЧИ (Celery + Redis)
# -------------------------------------------------------------------
# На Render Redis можно подключить как отдельный сервис
CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# -------------------------------------------------------------------
# БЕЗОПАСНОСТЬ (раскомментировать при деплое на продакшен)
# -------------------------------------------------------------------
# if not DEBUG:
#     SECURE_SSL_REDIRECT = True
#     SESSION_COOKIE_SECURE = True
#     CSRF_COOKIE_SECURE = True
#     SECURE_BROWSER_XSS_FILTER = True
#     SECURE_CONTENT_TYPE_NOSNIFF = True
#     X_FRAME_OPTIONS = 'DENY'

# -------------------------------------------------------------------
# EMAIL (для отправки уведомлений)
# -------------------------------------------------------------------
# Настройки для продакшена (раскомментировать и заполнить)
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.yandex.ru')
# EMAIL_PORT = int(os.getenv('EMAIL_PORT', 465))
# EMAIL_USE_SSL = True
# EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
# EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
# DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@rgsu-dorm.ru')

# Для локальной отладки письма выводятся в консоль
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# -------------------------------------------------------------------
# LOGGING (опционально, для отладки на сервере)
# -------------------------------------------------------------------
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'django': {
        'handlers': ['console'],
        'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        'propagate': False,
    },
}