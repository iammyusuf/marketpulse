from django.conf import settings
from django.db import models


class ScanEvent(models.Model):
    """Одно сканирование штрихкода одним работником, на одном складе, по одному товару."""

    worker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="scan_events",
        verbose_name="работник",
    )
    shop = models.ForeignKey(
        "organizations.Shop",
        on_delete=models.CASCADE,
        related_name="scan_events",
        verbose_name="склад",
    )
    product = models.ForeignKey(
        "integrations.Product",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="scan_events",
        verbose_name="товар",
        help_text="Пусто, если штрихкод ещё не встречался в синхронизированном каталоге товаров.",
    )
    raw_barcode = models.CharField(max_length=64, verbose_name="штрихкод")
    scanned_at = models.DateTimeField(auto_now_add=True, verbose_name="время сканирования")
    is_duplicate = models.BooleanField(default=False, verbose_name="дубликат")

    class Meta:
        ordering = ["-scanned_at"]
        indexes = [
            models.Index(fields=["shop", "scanned_at"]),
            models.Index(fields=["worker", "scanned_at"]),
        ]

    def __str__(self):
        return f"{self.raw_barcode} by {self.worker} @ {self.scanned_at:%Y-%m-%d %H:%M}"

    @classmethod
    def record_scan(cls, *, worker, shop, raw_barcode: str) -> "ScanEvent":
        """
        Создаёт ScanEvent для отсканированного штрихкода, сопоставляя его с
        синхронизированным каталогом товаров и помечая повторные сканирования
        за тот же день как дубликаты вместо того, чтобы молча их отбрасывать —
        дубликаты всё равно полезны как данные (например, чтобы поймать
        работника, случайно отсканировавшего одну и ту же коробку дважды).
        """
        from django.utils import timezone

        from integrations.models import Product

        product = Product.objects.filter(barcode=raw_barcode).first()

        already_scanned_today = cls.objects.filter(
            shop=shop,
            raw_barcode=raw_barcode,
            scanned_at__date=timezone.now().date(),
        ).exists()

        return cls.objects.create(
            worker=worker,
            shop=shop,
            product=product,
            raw_barcode=raw_barcode,
            is_duplicate=already_scanned_today,
        )
