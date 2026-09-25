import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "dev-only-secret-key-not-for-production"

DEBUG = True

ALLOWED_HOSTS = ["*"]

# MVP: no database, no auth, no sessions. Just enough apps for templating
# and static files.
INSTALLED_APPS = [
    "django.contrib.staticfiles",
    "orders",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "care_plan_service.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
            ],
        },
    },
]

WSGI_APPLICATION = "care_plan_service.wsgi.application"

# No database in this MVP — data lives in an in-memory dict (see orders/views.py).
DATABASES = {}

STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# MVP logging: everything at INFO and above goes to the console (visible via
# `docker compose logs` or `docker compose up`). A real deployment would add
# a file/CloudWatch handler here too.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}
