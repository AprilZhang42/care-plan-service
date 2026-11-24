import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "care_plan_service.settings")

app = Celery("care_plan_service")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()