"""
Django settings for fleet_management project.
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-f2c3$5tc4%4wb65+xf!(fjg=lwzq7%-j_(3#(+65g2xz9ky)ua'

DEBUG = True

ALLOWED_HOSTS = []


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
    'maintainance',
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


STATIC_URL = 'static/'

AUTH_USER_MODEL = 'accounts.User'

# ==============================
# ✅ NOTIFICATION SYSTEM FIX
# ==============================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==============================
# 🔥 MPESA DARAJA CONFIG (PRODUCTION READY)
# ==============================

MPESA_ENVIRONMENT = "sandbox"  # change to "production" when live

MPESA_CONSUMER_KEY = "G2HU6Sfcnq160p8D5tYPp8LrVAdgftqJ6gipBC5lHh7d4Eyo"
MPESA_CONSUMER_SECRET = "rZDsUn1GcnoDFJbVoZKfFmR075S9ZBZAV0HJzfgaGNBBwcsehTcCfhirsBJwLwFm"

# 🔥 IMPORTANT: Use correct shortcode per environment
MPESA_SHORTCODE = "174379"  # sandbox test shortcode
MPESA_PASSKEY = "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919"

# ==============================
# 🔥 CALLBACK CONFIGURATION
# ==============================

# ⚠️ IMPORTANT:
# These MUST be publicly accessible URLs in production (NOT localhost)

MPESA_CALLBACK_URL = "https://freddy-porkiest-rumblingly.ngrok-free.dev/mpesa/callback/"
MPESA_TIMEOUT_URL = "https://yourdomain.com/payments/mpesa/timeout/"

# ==============================
# 🔥 SECURITY + FORMAT RULES
# ==============================

MPESA_COUNTRY_CODE = "254"

# Force consistent phone normalization across system
MPESA_PHONE_FORMAT = "E164"  # internal standard

# ==============================
# 🔥 DEBUG HELP (SAFE FOR DEV)
# ==============================

MPESA_DEBUG = True


