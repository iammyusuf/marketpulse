from decimal import Decimal

import requests

from .base import MarketplaceClient

WB_PRODUCTS_URL = "https://suppliers-api.wildberries.ru/content/v2/get/cards/list"


class WildberriesClient(MarketplaceClient):
    """
    Тонкая обёртка над API продавца Wildberries.

    ВАЖНО: точный эндпоинт и форма ответа должны быть перепроверены по
    актуальной документации Wildberries API перед использованием в продакшене —
    маркетплейсы довольно часто меняют контракты своих API без предупреждения.
    Этот класс изолирует такую нестабильность в одном файле.
    """

    def fetch_products(self) -> list[dict]:
        response = requests.post(
            WB_PRODUCTS_URL,
            headers={"Authorization": self.api_key},
            json={"settings": {"cursor": {"limit": 100}, "filter": {"withPhoto": -1}}},
            timeout=15,
        )
        response.raise_for_status()
        payload = response.json()

        products = []
        for card in payload.get("cards", []):
            for size in card.get("sizes", []):
                for barcode in size.get("skus", []):
                    products.append(
                        {
                            "barcode": barcode,
                            "external_id": str(card.get("nmID", "")),
                            "name": card.get("title", "Товар без названия"),
                            "rate_per_unit": Decimal("0"),
                        }
                    )
        return products
