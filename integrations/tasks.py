import logging

from celery import shared_task
from django.utils import timezone

from .models import MarketplaceConnection, Product
from .services.factory import get_client

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def sync_products_for_connection(self, connection_id: int):
    """Забирает актуальный список товаров по одному подключению и обновляет каталог."""
    try:
        connection = MarketplaceConnection.objects.get(pk=connection_id, is_active=True)
    except MarketplaceConnection.DoesNotExist:
        logger.warning(
            "Подключение %s не найдено или неактивно, синхронизация пропущена.", connection_id
        )
        return

    try:
        client = get_client(connection.marketplace, connection.api_key)
        products = client.fetch_products()
    except Exception as exc:
        logger.exception("Синхронизация не удалась для подключения %s", connection_id)
        raise self.retry(exc=exc)

    for item in products:
        Product.objects.update_or_create(
            connection=connection,
            barcode=item["barcode"],
            defaults={
                "external_id": item.get("external_id", ""),
                "name": item.get("name", ""),
                "rate_per_unit": item.get("rate_per_unit", 0),
            },
        )

    connection.last_synced_at = timezone.now()
    connection.save(update_fields=["last_synced_at"])
    logger.info("Синхронизировано %s товаров для подключения %s", len(products), connection_id)


@shared_task
def sync_all_active_connections():
    """Периодическая точка входа — запускается каждую минуту через Celery beat,
    расходится по отдельной задаче на каждое подключение."""
    connection_ids = MarketplaceConnection.objects.filter(is_active=True).values_list(
        "id", flat=True
    )
    for connection_id in connection_ids:
        sync_products_for_connection.delay(connection_id)
