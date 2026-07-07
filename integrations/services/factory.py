from ..models import Marketplace
from .base import MarketplaceClient
from .wildberries import WildberriesClient


def get_client(marketplace: str, api_key: str) -> MarketplaceClient:
    clients = {
        Marketplace.WILDBERRIES: WildberriesClient,
        # Marketplace.UZUM: UzumClient,  # добавить, как только появится реализация для Uzum
    }
    client_class = clients.get(marketplace)
    if client_class is None:
        raise NotImplementedError(f"Клиент для маркетплейса '{marketplace}' не реализован")
    return client_class(api_key=api_key)
