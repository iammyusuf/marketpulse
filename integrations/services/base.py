from abc import ABC, abstractmethod


class MarketplaceClient(ABC):
    """
    Общий интерфейс, который должна реализовать каждая интеграция с маркетплейсом.
    Чтобы добавить новый маркетплейс (Ozon и т.д.), достаточно написать один
    новый класс здесь — остальной код проекта менять не нужно.
    """

    def __init__(self, api_key: str):
        self.api_key = api_key

    @abstractmethod
    def fetch_products(self) -> list[dict]:
        """
        Возвращает список словарей вида:
        {"barcode": str, "external_id": str, "name": str, "rate_per_unit": Decimal}
        """
        raise NotImplementedError
