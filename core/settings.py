"""
Django settings for social_platform project.

Is file mein humari website ki saari configurations hain.
Har setting ke saath comment hai jo batata hai yeh kya karta hai.
"""

import os
from pathlib import Path
import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
# BASE_DIR = project root folder (jahan manage.py hai)
BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================
# ENVIRONMENT VARIABLES SETUP
# ============================================
# WHAT: .env file se sensitive values load karta hai
# WHY: Passwords aur secret keys code mein hardcode nahi karte - security risk

env = environ.Env(
    # Default values agar .env file mein na ho
    DEBUG=(bool, False),
    SECRET_KEY=(str, 'fallback-secret-key-change-me'),
    ALLOWED_HOSTS=(list, ['localhost', '127.0.0.1']),
)

# .env file read karo (agar exist karta hai)
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# ============================================
# CORE DJANGO SETTINGS
# ============================================

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG')

ALLOWED_HOSTS = env('ALLOWED_HOSTS')

# Production pe HTTPS forms ke liye zaruri (login/signup broken hoga iske bina)
_csrf_origins = os.environ.get('CSRF_TRUSTED_ORIGINS', '')
CSRF_TRUSTED_ORIGINS = [o.strip() for o in _csrf_origins.split(',') if o.strip()]

# Automatic Railway environment setup for CSRF
railway_domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN')
if railway_domain:
    domain_url = f"https://{railway_domain}"
    if domain_url not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(domain_url)



# ============================================
# APPLICATION DEFINITION
# ============================================
# WHAT: Kaunse Django apps installed hain
# WHY: Har app ke models, views, URLs project mein include hote hain

INSTALLED_APPS = [
    'unfold',  # ⭐ Unfold must be first!
    # Django built-in apps (free features)
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',       # Required for django-allauth
    
    # Third-party apps (hum install karte hain)
    'allauth',                    # Complete auth system
    'allauth.account',            # User accounts
    'allauth.socialaccount',      # Social login (Google, etc.)
    
    # Our custom apps (aage banayenge)
    # 'accounts',
    # 'feed',
    # 'reels',
    # ... baaki apps
    # Our custom apps
    'accounts',  # ⭐ YEH LINE ADD KARO
    'feed',  # ⭐ YEH LINE ADD KAR
    'reels',  # ⭐ YEH LINE ADD KARO
    'research',  # ⭐ YEH LINE ADD KARO
    'jobs',  # ⭐ YEH LINE ADD KARO
    'webinars',  # ⭐ YEH LINE ADD KARO
    'groups',  # ⭐ YEH LINE ADD KARO
    'chat',  # ⭐ YEH LINE ADD KARO
    'user_notifications',  # ⭐ ADD THIS
    'search_app',  # ⭐ ADD THIS
    'monetization',  # ⭐ ADD THIS
    'rest_framework',  # ⭐ REST Framework for API
    'rest_framework_simplejwt',  # ⭐ JWT Authentication for APIs
    'rest_framework_simplejwt.token_blacklist',  # ⭐ JWT Token Blacklist (required for BLACKLIST_AFTER_ROTATION)
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Static files serve karta hai bina separate server ke
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',        # Hindi/English language support
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',     # Required for django-allauth
    'monetization.middleware.ConsentMiddleware',       # ⭐ ADD THIS FOR GDPR MONETIZATION CONSENT
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # Custom templates folder
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

WSGI_APPLICATION = 'core.wsgi.application'
ASGI_APPLICATION = 'core.asgi.application'  # Real-time features ke liye


# ============================================
# DATABASE CONFIGURATION
# ============================================
# WHAT: Database connection settings
# WHY: Data store karne ke liye (users, posts, etc.)
# Abhi SQLite use karenge (free, no setup), baad mein PostgreSQL

import sys
if 'test' in sys.argv:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': env.db('DATABASE_URL', default='sqlite:///db.sqlite3')  # type: ignore
    }


# ============================================
# PASSWORD VALIDATION
# ============================================
# WHAT: Password strength rules
# WHY: Security - weak passwords hack ho sakte hain

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8},
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# ============================================
# INTERNATIONALIZATION (i18n)
# ============================================
# WHAT: Multiple language support
# WHY: Hindi + English dono support karenge

LANGUAGE_CODE = 'en-us'

# Hindi language add karo
LANGUAGES = [
    ('en', 'English'),
    ('hi', 'Hindi'),
]

# Translation files kahan store honge
LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

TIME_ZONE = 'Asia/Kolkata'  # India timezone

USE_I18N = True
USE_TZ = True


# ============================================
# STATIC FILES (CSS, JavaScript, Images)
# ============================================
# WHAT: CSS, JS, Images files ka URL aur storage location
# WHY: Website styling aur media uploads ke liye

STATIC_URL = 'static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',  # Custom static files
]
STATIC_ROOT = BASE_DIR / 'staticfiles'  # Production mein collected files
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'  # CSS/JS compress + cache karta hai

# Media files (User uploaded images, videos)
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'


# ============================================
# DEFAULT PRIMARY KEY FIELD TYPE
# ============================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ============================================
# AUTHENTICATION SETTINGS (django-allauth)
# ============================================
# WHAT: Custom authentication behavior
# WHY: Email-based login, email verification required

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Allauth settings - DJANGO 6.x COMPATIBLE VERSION
# WHAT: Django 6.x mein yeh settings change ho gayi hain
# WHY: Naye version mein zyada flexible signup configuration

ACCOUNT_FORMS = {
    'signup': 'accounts.forms.CustomSignupForm',  # Fallback for admin/social login
}
ACCOUNT_ADAPTER = 'accounts.adapter.AccountAdapter'

ACCOUNT_LOGIN_METHODS = {'email'}  # Email se login hoga (NEW in Django 6.x)
ACCOUNT_EMAIL_VERIFICATION = 'optional'  # Our custom OTP handles verification
ACCOUNT_SIGNUP_FIELDS = ['email*', 'username*', 'password1*', 'password2*']  # NEW format

# ⭐ Custom signup URL — allauth ke /accounts/signup/ ko hamare /accounts/register/ par redirect karo
ACCOUNT_SIGNUP_URL = '/accounts/register/'

LOGIN_REDIRECT_URL = '/'            # Login ke baad kahan jaoge
LOGOUT_REDIRECT_URL = '/'           # Logout ke baad kahan jaoge

# Email Settings (Gmail SMTP)
EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend').strip()  # type: ignore
EMAIL_HOST = env.str('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
EMAIL_HOST_USER = env.str('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env.str('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env.str('EMAIL_HOST_USER', default='noreply@socialplatform.com')

# Optional but recommended
ACCOUNT_USERNAME_MIN_LENGTH = 3
ACCOUNT_PASSWORD_MIN_LENGTH = 8
ACCOUNT_LOGOUT_ON_GET = True  # Logout ke liye confirmation page skip karo
SITE_ID = 1


# ============================================
# CUSTOM USER MODEL
# ============================================
AUTH_USER_MODEL = 'accounts.User'  # ⭐ Batata hai ki humara custom User model kaunsa hai




# ============================================
# DJANGO CHANNELS CONFIGURATION
# ============================================
# WHAT: WebSocket support for real-time features
# WHY: Chat aur notifications ke liye

INSTALLED_APPS += [
    'channels',
]


import sys
if 'test' in sys.argv or DEBUG:
    # Local dev or tests: use in-memory channel layer (no Redis needed)
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
        },
    }
else:
    # Production: use Redis for scalable WebSocket support
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {
                'hosts': [env.str('REDIS_URL', default='redis://127.0.0.1:6379')],  # Railway Redis URL
            },
        },
    }

# ============================================
# API AND SIMPLEJWT SECURITY CONFIGURATION
# ============================================
# WHAT: Configures REST Framework and JWT Token settings
# WHY: Secure mobile API authentication & authorization
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}

from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
}
