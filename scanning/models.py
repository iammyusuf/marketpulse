from django.conf import settings
from django.db import models


class Device(models.Model):
    """Сканирующее устройство (терминал сбора данных), закреплённое за складом."""

    shop = models.ForeignKey(
        "organizations.Shop", on_delete=models.CASCADE, related_name="devices", verbose_name="склад"
    )
    assigned_worker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_devices",
        verbose_name="закреплённый работник",
    )
    identifier = models.CharField(max_length=64, unique=True, verbose_name="идентификатор устройства")
    is_active = models.BooleanField(default=True, verbose_name="активно")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="создано")

    class Meta:
        ordering = ["identifier"]

    def __str__(self):
        return f"{self.identifier} ({self.shop.name})"


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
    device = models.ForeignKey(
        Device,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="scan_events",
        verbose_name="устройство",
    )
    raw_barcode = models.CharField(max_length=64, verbose_name="штрихкод")
    scanned_at = models.DateTimeField(auto_now_add=True, verbose_name="время сканирования")
    is_duplicate = models.BooleanField(default=False, verbose_name="дубликат")
    is_device_mismatch = models.BooleanField(
        default=False,
        verbose_name="несоответствие устройства",
        help_text="Скан выполнен с устройства, закреплённого за другим работником.",
    )
    unit_rate_snapshot = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="ставка за единицу на момент сканирования",
    )

    class Meta:
        ordering = ["-scanned_at"]
        indexes = [
            models.Index(fields=["shop", "scanned_at"]),
            models.Index(fields=["worker", "scanned_at"]),
        ]

    def __str__(self):
        return f"{self.raw_barcode} by {self.worker} @ {self.scanned_at:%Y-%m-%d %H:%M}"

    @classmethod
    def record_scan(cls, *, worker, shop, raw_barcode: str, device_identifier: str | None = None) -> "ScanEvent":
        """
        Создаёт ScanEvent для отсканированного штрихкода, сопоставляя его с
        синхронизированным каталогом товаров и помечая повторные сканирования
        за тот же день как дубликаты вместо того, чтобы молча их отбрасывать —
        дубликаты всё равно полезны как данные (например, чтобы поймать
        работника, случайно отсканировавшего одну и ту же коробку дважды).

        Если передан device_identifier, устройство привязывается к скану, а
        несовпадение с закреплённым за устройством работником лишь помечается
        флагом (is_device_mismatch) для последующего разбора, а не блокирует
        сканирование.

        Ставка за единицу берётся из текущего тарифа работника и сохраняется
        в unit_rate_snapshot на момент скана — последующее изменение тарифа
        не должно задним числом менять уже посчитанный заработок.
        """
        from django.utils import timezone

        from integrations.models import Product
        from payroll.models import PayType, Tariff

        product = Product.objects.filter(barcode=raw_barcode).first()

        device = None
        is_device_mismatch = False
        if device_identifier:
            device = Device.objects.filter(identifier=device_identifier, shop=shop).first()
            if device and device.assigned_worker_id and device.assigned_worker_id != worker.id:
                is_device_mismatch = True

        already_scanned_today = cls.objects.filter(
            shop=shop,
            raw_barcode=raw_barcode,
            # scanned_at__date конвертирует значение в текущий TIME_ZONE перед
            # сравнением, поэтому здесь нужна localdate(), а не now().date()
            # (которая возвращает дату в UTC) — иначе они расходятся вечером по UTC.
            scanned_at__date=timezone.localdate(),
        ).exists()

        tariff = Tariff.current_for(worker, pay_type=PayType.PER_UNIT)

        return cls.objects.create(
            worker=worker,
            shop=shop,
            product=product,
            device=device,
            raw_barcode=raw_barcode,
            is_duplicate=already_scanned_today,
            is_device_mismatch=is_device_mismatch,
            unit_rate_snapshot=tariff.rate if tariff else None,
        )
