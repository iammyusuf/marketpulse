from django.conf import settings
from django.db import models
from django.utils import timezone


class PayType(models.TextChoices):
    PER_UNIT = "per_unit", "За единицу"
    HOURLY = "hourly", "Почасовая"
    FIXED_MONTHLY = "fixed_monthly", "Фиксированная (в месяц)"


class Tariff(models.Model):
    """
    Ставка оплаты сотрудника. Ведётся с историей (effective_from), а не одним
    текущим значением — иначе прошлые периоды в сводке продуктивности задним
    числом пересчитывались бы по новой ставке при её изменении, повторяя ровно
    ту же проблему, что и Product.rate_per_unit (перезаписывается синхронизацией).
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tariffs", verbose_name="сотрудник"
    )
    pay_type = models.CharField(max_length=20, choices=PayType.choices, verbose_name="тип оплаты")
    rate = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="ставка")
    effective_from = models.DateField(verbose_name="действует с")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_tariffs",
        verbose_name="кем установлено",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="создано")

    class Meta:
        ordering = ["-effective_from", "-id"]
        indexes = [models.Index(fields=["user", "effective_from"])]

    def __str__(self):
        return f"{self.user} — {self.get_pay_type_display()} {self.rate} (с {self.effective_from})"

    @classmethod
    def current_for(cls, user, *, pay_type=None, on_date=None):
        on_date = on_date or timezone.now().date()
        qs = cls.objects.filter(user=user, effective_from__lte=on_date)
        if pay_type:
            qs = qs.filter(pay_type=pay_type)
        return qs.order_by("-effective_from", "-id").first()


class Shift(models.Model):
    """Смена/рабочие часы одного работника на одном складе."""

    worker = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="shifts", verbose_name="работник"
    )
    shop = models.ForeignKey(
        "organizations.Shop", on_delete=models.CASCADE, related_name="shifts", verbose_name="склад"
    )
    started_at = models.DateTimeField(verbose_name="начало смены")
    ended_at = models.DateTimeField(null=True, blank=True, verbose_name="конец смены")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_shifts",
        verbose_name="кем создано/изменено",
    )
    note = models.CharField(max_length=255, blank=True, verbose_name="примечание")

    class Meta:
        ordering = ["-started_at"]
        indexes = [
            models.Index(fields=["shop", "started_at"]),
            models.Index(fields=["worker", "started_at"]),
        ]

    def __str__(self):
        return f"{self.worker} @ {self.shop} ({self.started_at:%Y-%m-%d %H:%M})"

    @property
    def duration_hours(self):
        if not self.ended_at:
            return None
        return round((self.ended_at - self.started_at).total_seconds() / 3600, 2)
