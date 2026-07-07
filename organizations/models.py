from django.conf import settings
from django.db import models


class Organization(models.Model):
    """
    Арендатор (tenant) платформы — один бизнес/продавец.
    Всё остальное (склады, подключения к маркетплейсам, пользователи)
    привязано именно к этой сущности.
    """

    name = models.CharField(max_length=255, verbose_name="название")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="owned_organizations",
        verbose_name="владелец",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="создано")

    def __str__(self):
        return self.name


class Shop(models.Model):
    """Физический склад/точка упаковки, принадлежащая организации."""

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="shops", verbose_name="организация"
    )
    name = models.CharField(max_length=255, verbose_name="название")
    description = models.TextField(blank=True, verbose_name="описание")
    is_active = models.BooleanField(default=True, verbose_name="активен")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="создано")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.organization.name})"
