"""
Django settings for mysite project.

Generated by 'django-admin startproject' using Django 4.2.1.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

from pathlib import Path
import os
import sys
import tzlocal

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(
    os.environ.get('PLAYER_DIR', Path(__file__).resolve().parent.parent)
)

TEST = 'test' in sys.argv


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = bool(int(os.environ.get('PLAYER_DEBUG', 1)))

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'etc_player',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
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

ROOT_URLCONF = 'etc_player.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'etc_player.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'ATOMIC_REQUESTS': True
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = tzlocal.get_localzone_name()

USE_I18N = True

USE_TZ = False


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

RESTART_COMMAND = 'sudo systemctl restart audio'

VOLUME_COMMAND = 'sudo amixer sset PCM -M {volume}%'

# when not running as root - this command would work - Master not available as
# root
# VOLUME_COMMAND = 'amixer sset Master {volume}%'

PLAY_COMMAND = 'aplay {wave_file}'

STATIC_ROOT = BASE_DIR / 'static'
MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_URL = 'media/'

# rwx for user and group
FILE_UPLOAD_PERMISSIONS = 0o770
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o770

SECRETS_DIR = Path(BASE_DIR) / 'secrets'


def generate_secret_key(filename):
    from django.core.management.utils import get_random_secret_key
    with open(filename, 'w') as f:
        f.write("%s\n" % get_random_secret_key())
    os.chmod(filename, 0o640)


def get_secret_key(filename):
    with open(filename, 'r') as f:
        return f.readlines()[0]


if not os.path.exists(SECRETS_DIR):
    os.makedirs(SECRETS_DIR)


sk_file = os.path.join(SECRETS_DIR, 'secret_key')

if not os.path.exists(sk_file):
    generate_secret_key(sk_file)

SECRET_KEY = get_secret_key(sk_file)

if len(SECRET_KEY) == 0:
    generate_secret_key(sk_file)
    SECRET_KEY = get_secret_key(sk_file)
