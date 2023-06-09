import os
from pathlib import Path

from django.contrib.messages import constants as messages
from huey import RedisHuey
from redis import ConnectionPool

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '*gvv@$t-ntphhapwc_(@+gz#!ehvz^nhzc850w(6-7p2ig%ce#'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts.apps.AccountsConfig',
    'utils.apps.UtilsConfig',
    'mpesa.apps.MpesaConfig',
    'spinwin.apps.SpinwinConfig',
    'custom_admin.apps.CustomAdminConfig',
    'tasks_feature.apps.TasksFeatureConfig',
    'flutterwave.apps.FlutterwaveConfig',
    'channels',
    'huey.contrib.djhuey',
    'django_cleanup.apps.CleanupConfig',
]

MESSAGE_TAGS = {
    messages.DEBUG: 'alert-info',
    messages.INFO: 'alert-info',
    messages.SUCCESS: 'alert-success',
    messages.WARNING: 'alert-warning',
    messages.ERROR: 'alert-danger',
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'online_marketing.urls'

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

WSGI_APPLICATION = 'online_marketing.wsgi.application'
ASGI_APPLICATION = "online_marketing.routing.application"

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'earnsasa',
        'USER': 'mwaniki',
    'PASSWORD':'tori',
    }
}

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],
        },
    },
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.PyMemcacheCache',
        'LOCATION': '127.0.0.1:11211',
    }
}

# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Authentication backends
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = '/static/'
# STATIC_ROOT = BASE_DIR / 'static'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files
# MEDIA_URL = '/media/'
# MEDIA_ROOT = '/var/www/online_marketing/media'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Accounts
AUTH_USER_MODEL = 'accounts.User'
LOGIN_REDIRECT_URL = 'user_dashboard'
LOGIN_URL = 'login'
LOGOUT_REDIRECT_URL = 'index'

# M-pesa
MPESA_C2B_SHORTCODE = '4085083'
MPESA_C2B_CONSUMER_KEY = "vih1S3jZtudozY3rExJ8rGxUsANiAa11"
MPESA_C2B_CONSUMER_SECRET = "Sjoiw9Dgfyftj4sp"
MPESA_C2B_INITIATOR = 'josephApi2'
MPESA_C2B_SECURITY_CREDENTIAL = "ga93CD8JI1EiEFnelq6my1pF0829zGFlfmvHeZzr4IJx0XBJAXvzTK+1V64dFQzukugHniPFdM47v3LBeSGIzRNvJXF+qzHl3/v7lFomP5g9wuiIORqIDLlBqS/DFzLS3jXKDMSyA8GzpOsX7MaDyz7Wpo+PR7KFZsMFu5X7oB28K0yTYvdRpO9Xd/zWrhxE0nRYTOUwUq2vovSr4+iZxsrdnQTldhWLILY+ZVfe77KS8gZ2vVJ4XQItot9rmdiQnJtMrH38h61v0t1+7zGSabM2uvqkEQpFKLM+xZVlWoDV67p4VTxoOSh4gaPd2mUxfQpbaZ63mSpgo9nMXtLKZg=="
LIPA_NA_MPESA_PASSKEY = "8364178161dc48f2246b7987e3e404de911ef88851ffca7ed81d438ba1d88c41"
MPESA_B2C_SHORTCODE = '3030153'
MPESA_B2C_INITIATOR_NAME = 'gardeAPI2'
MPESA_B2C_CONSUMER_KEY = 'xtnGKJlNQmwpdBLaoScecz6Hek9NlSAp'
MPESA_B2C_CONSUMER_SECRET = '6GjOvTai7LrCm1nq'
MPESA_B2C_INITIATOR_CREDENTIAL = 'ocQmvyLPBzk7GwnpYU0u9UZfpWkZnJIxvwyjmmj9Y3Jy8dn1AGxfS+t/b24cIFSsdtgj0ovuVWCrj04V+kMs7YHo+9/uG+SHIFS4yd/4rBSuCF9JJEDj8kvsz7bwmSOK2eVMU+hPyReMZl4rBPX6FnV5JyKnjRv8Ty/76eIiQaGY2DhAO1Ae5b6mllHRlC3kd3Rl6gvzgUxP6t3kW6dmEfdtICaF8llYYDHQmET4aywwRotCPrPSBTdmpVsZH9+jPcuMe6wMeO7G3kb8rtrvO5NItC8EVChj3DWr6WSOCbtTMZkiLuw8EKhtlTb68M+HI4LyyQ16uGBgSiBoevqZ4w=='
MPESA_SECRET = 'nrCpCSOyldGWxhJ4HGXAByHd577lDb6zO03DK2de_vviNR_lc1c2IXl8Sxc1fPW2_jS1Q41ODnN_5zG2'

# Celery config
CELERY_BROKER_URL = 'redis://localhost:6379'
CELERY_result_backend = 'redis://localhost:6379'
CELERY_accept_content = ['application/json']
CELERY_result_serializer = 'json'
CELERY_task_serializer = 'json'

# ElphWays
ELPHWAYS_API_KEY = 'PIAqbKuwHtXn13fg9ecqaVliW976lrT7YzgxEYry0UV98SVRirKp02T26EP7Nyp1'
ELPHWAYS_SENDER_ID = '23107'

# More
SITE_NAME = 'EasyEarn'
MIN_WITHDRAWAL = 500
WITHDRAWAL_CHARGE = 25
MIN_SPINWIN_TOP_UP = 20
SPINWIN_CHARGE = 20

# Referral
ACTIVATION_AMOUNT = 100
REFERRAL_BONUS = 50

# Tasks feature
TASKS_PACKAGES = {
    'BRONZE': {
        'price': 1000,  # In KES
        'income_per_task': 7,  # In KES
        'tasks_per_day': 10,
        'validity': 30,  # In days
    },
    'SILVER': {
        'price': 3000,  # In KES
        'income_per_task': 13,  # In KES
        'tasks_per_day': 13,
        'validity': 30,  # In days
    },
    'GOLD': {
        'price': 8000,  # In KES
        'income_per_task': 15,  # In KES
        'tasks_per_day': 15,
        'validity': 90,  # In days
    },
    'PLATINUM': {
        'price': 21000,  # In KES
        'income_per_task': 25,  # In KES
        'tasks_per_day': 30,
        'validity': 180,  # In days
    },
}
MIN_TASKS_WALLET_TRANSFER = 1900

# Huey
pool = ConnectionPool(host='127.0.0.1', port=6379, max_connections=20)
HUEY = RedisHuey('online_marketing', connection_pool=pool)

# Exchange rates
FREE_CURRENCY_API_KEY = 'YOUR_KEY'

# Flutterwave
FLUTTERWAVE_PUBLIC_KEY = 'FLWPUBK-7b494812e3aeb09395b41cf588ac50f8-X'
FLUTTERWAVE_SECRET_KEY = 'FLWSECK-21775462bd33c78fd0420d65ab637115-X'
FLUTTERWAVE_ENCRYPTION_KEY = '21775462bd33cf97dbbc7896'
