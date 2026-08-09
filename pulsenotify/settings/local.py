"""Local development settings."""
from .base import *  # noqa: F401, F403

DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'pulsenotify'),
        'USER': os.environ.get('DB_USER', 'pulsenotify'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'pulsenotify'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}
