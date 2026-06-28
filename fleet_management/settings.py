"""
Django settings for fleet_management project.
"""
import os


from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent



# ================================
# SECURITY
# ================================
SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "django-insecure-dev-key"
)

# False on Vercel / production
DEBUG = os.getenv("VERCEL") is None

ALLOWED_HOSTS = [
    ".vercel.app",
    "localhost",
    "127.0.0.1",
]




INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Apps
    'accounts',
    'loans',
    'drivers',
    'maintenance',
    'notifications',
    'payments',
    'reports',
    'vehicles',
]


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'fleet_management.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'notifications.context_processors.notification_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'fleet_management.wsgi.application'


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Africa/Nairobi'   # ✅ FIXED (important for real system)

USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)

STATIC_URL = '/static/'

STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

AUTH_USER_MODEL = 'accounts.User'

# ==============================
# ✅ NOTIFICATION SYSTEM FIX
# ==============================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'



# ── Auto logout after 5 minutes of inactivity ──
SESSION_COOKIE_AGE = 300              # 5 minutes in seconds
SESSION_SAVE_EVERY_REQUEST = True     # reset timer on every request
SESSION_EXPIRE_AT_BROWSER_CLOSE = True  # also logout when browser closes
