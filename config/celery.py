import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

app = Celery("marketpulse")
# Настройки Celery берутся из настроек Django с префиксом CELERY_.
app.config_from_object("django.conf:settings", namespace="CELERY")
# Автоматически находит tasks.py во всех установленных приложениях.
app.autodiscover_tasks()
