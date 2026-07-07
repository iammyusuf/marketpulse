from .dev import *  # noqa

# Быстрый (но небезопасный) хешер паролей — ускоряет тесты в разы.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Celery-задачи выполняются синхронно (брокер не требуется) во время тестов.
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
