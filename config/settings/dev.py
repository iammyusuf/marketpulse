from .base import *  # noqa
from .base import BASE_DIR, env  # noqa

# Локальная разработка без Docker использует SQLite — не нужен запущенный PostgreSQL.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

CORS_ALLOW_ALL_ORIGINS = True
