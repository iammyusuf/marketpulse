from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.TextChoices):
    OWNER = "owner", "Владелец"
    MANAGER = "manager", "Менеджер"
    WORKER = "worker", "Работник склада"


class CustomUser(AbstractUser):
    """
    Кастомная модель пользователя. Каждый пользователь может (не обязательно)
    принадлежать одной организации (бизнесу/продавцу, использующему платформу)
    с определённой ролью.

    Встроенные флаги Django `is_superuser` / `is_staff` используются для
    администраторов самой платформы — они не связаны с бизнес-ролью `role` ниже.
    """

    phone = models.CharField(max_length=20, blank=True, verbose_name="телефон")
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="members",
        verbose_name="организация",
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.WORKER,
        verbose_name="роль",
    )

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.role})"

    @property
    def is_owner(self):
        return self.role == Role.OWNER

    @property
    def is_manager(self):
        return self.role == Role.MANAGER
