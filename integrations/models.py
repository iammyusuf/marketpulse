from django.db import models


class Marketplace(models.TextChoices):
    WILDBERRIES = "wildberries", "Wildberries"
    UZUM = "uzum", "Uzum Market"


class MarketplaceConnection(models.Model):
    """
    Учётные данные одной организации для синхронизации с конкретным
    маркетплейсом. API-ключ читается отсюда только на сервере — он никогда
    не отдаётся на фронтенд, не логируется и не коммитится в git.
    """

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="marketplace_connections",
        verbose_name="организация",
    )
    marketplace = models.CharField(
        max_length=20, choices=Marketplace.choices, verbose_name="маркетплейс"
    )
    api_key = models.CharField(max_length=255, verbose_name="API-ключ")
    is_active = models.BooleanField(default=True, verbose_name="активно")
    last_synced_at = models.DateTimeField(
        null=True, blank=True, verbose_name="последняя синхронизация"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="создано")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "marketplace"], name="unique_connection_per_marketplace"
            )
        ]

    def __str__(self):
        return f"{self.organization.name} — {self.get_marketplace_display()}"


class Product(models.Model):
    """Товар, каким его знает маркетплейс — синхронизируется периодически через Celery."""

    connection = models.ForeignKey(
        MarketplaceConnection,
        on_delete=models.CASCADE,
        related_name="products",
        verbose_name="подключение",
    )
    barcode = models.CharField(max_length=64, db_index=True, verbose_name="штрихкод")
    external_id = models.CharField(max_length=128, blank=True, verbose_name="внешний ID")
    name = models.CharField(max_length=255, verbose_name="название")
    rate_per_unit = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name="ставка за единицу"
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name="обновлено")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["connection", "barcode"], name="unique_barcode_per_connection"
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.barcode})"
