import random
from datetime import datetime, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import CustomUser, Role
from integrations.models import Marketplace, MarketplaceConnection, Product
from organizations.models import Organization, Shop
from payroll.models import PayType, Shift, Tariff
from scanning.models import Device, ScanEvent

DEMO_PASSWORD = "demo12345"


class Command(BaseCommand):
    help = "Наполняет базу демо-данными для презентации/тестирования фронтенда."

    def handle(self, *args, **options):
        random.seed(42)

        org, _ = Organization.objects.get_or_create(name='ООО "Малика Трейд"')

        owner, _ = CustomUser.objects.get_or_create(
            username="demo_owner",
            defaults={"role": Role.OWNER, "organization": org, "first_name": "Малика", "last_name": "Юсупова"},
        )
        owner.set_password(DEMO_PASSWORD)
        owner.role = Role.OWNER
        owner.organization = org
        owner.first_name, owner.last_name = "Малика", "Юсупова"
        owner.save()
        org.owner = owner
        org.save(update_fields=["owner"])

        shop1, _ = Shop.objects.get_or_create(
            organization=org, name="Склад Чиланзар", defaults={"description": "Основной склад упаковки, Чиланзарский район"}
        )
        shop2, _ = Shop.objects.get_or_create(
            organization=org, name="Склад Юнусабад", defaults={"description": "Второй склад, Юнусабадский район"}
        )

        manager1 = self._upsert_user("demo_manager1", Role.MANAGER, org, shop1, "Дилноза", "Каримова")
        manager2 = self._upsert_user("demo_manager2", Role.MANAGER, org, shop2, "Сардор", "Алиев")

        worker_names_shop1 = [("Ботир", "Расулов"), ("Малика", "Эргашева"), ("Жавлон", "Тошев")]
        worker_names_shop2 = [("Нодира", "Исмоилова"), ("Шерзод", "Умаров"), ("Гулнора", "Алиева")]

        workers_shop1 = [
            self._upsert_user(f"demo_worker{i + 1}", Role.WORKER, org, shop1, fn, ln)
            for i, (fn, ln) in enumerate(worker_names_shop1)
        ]
        workers_shop2 = [
            self._upsert_user(f"demo_worker{i + 4}", Role.WORKER, org, shop2, fn, ln)
            for i, (fn, ln) in enumerate(worker_names_shop2)
        ]
        all_workers = workers_shop1 + workers_shop2

        wb_connection, _ = MarketplaceConnection.objects.get_or_create(
            organization=org, marketplace=Marketplace.WILDBERRIES, defaults={"api_key": "demo-wb-key", "is_active": True}
        )
        uzum_connection, _ = MarketplaceConnection.objects.get_or_create(
            organization=org, marketplace=Marketplace.UZUM, defaults={"api_key": "demo-uzum-key", "is_active": True}
        )

        product_catalog = [
            (wb_connection, "4600000000011", "Футболка базовая, черная, M", "1500.00"),
            (wb_connection, "4600000000028", "Футболка базовая, белая, L", "1500.00"),
            (wb_connection, "4600000000035", "Худи оверсайз, серый, XL", "3200.00"),
            (wb_connection, "4600000000042", "Джинсы прямые, синие, 32", "4500.00"),
            (uzum_connection, "4600000000059", "Платье летнее, цветочный принт", "2800.00"),
            (uzum_connection, "4600000000066", "Куртка ветровка, хаки", "3900.00"),
            (uzum_connection, "4600000000073", "Носки хлопковые, набор 3 пары", "450.00"),
        ]
        products = []
        for connection, barcode, name, rate in product_catalog:
            product, _ = Product.objects.get_or_create(
                connection=connection,
                barcode=barcode,
                defaults={"external_id": barcode, "name": name, "rate_per_unit": Decimal(rate)},
            )
            products.append(product)

        # Устройства — по одному на работника + пара свободных на каждом складе.
        devices_by_worker = {}
        for i, worker in enumerate(all_workers, start=1):
            device, _ = Device.objects.get_or_create(
                identifier=f"SCN-{i:03d}", defaults={"shop": worker.shop, "assigned_worker": worker}
            )
            devices_by_worker[worker.id] = device
        Device.objects.get_or_create(identifier="SCN-SPARE-1", defaults={"shop": shop1, "assigned_worker": None})
        Device.objects.get_or_create(identifier="SCN-SPARE-2", defaults={"shop": shop2, "assigned_worker": None})

        # localdate(), не now().date(): now().date() возвращает дату в UTC,
        # а сводка на фронтенде фильтрует по локальной дате (TIME_ZONE) —
        # расхождение около полуночи по UTC иначе оставляло "сегодня" пустым.
        today = timezone.localdate()

        # Тарифы: у большинства работников — сдельная оплата, у одного — почасовая,
        # чтобы на фронтенде было видно оба режима расчёта заработка.
        Tariff.objects.filter(user__in=all_workers + [manager1, manager2]).delete()
        for worker in all_workers:
            pay_type = PayType.HOURLY if worker.username == "demo_worker6" else PayType.PER_UNIT
            rate = Decimal("25000.00") if pay_type == PayType.HOURLY else Decimal(random.choice(["900", "1100", "1300"]))
            Tariff.objects.create(
                user=worker, pay_type=pay_type, rate=rate, effective_from=today - timedelta(days=30), created_by=owner
            )
        for manager in (manager1, manager2):
            Tariff.objects.create(
                user=manager,
                pay_type=PayType.FIXED_MONTHLY,
                rate=Decimal("4500000.00"),
                effective_from=today - timedelta(days=30),
                created_by=owner,
            )

        # Смены за последние 10 дней.
        Shift.objects.filter(worker__in=all_workers).delete()
        for worker in all_workers:
            for days_ago in range(9, -1, -1):
                day = today - timedelta(days=days_ago)
                start = timezone.make_aware(datetime.combine(day, datetime.min.time())) + timedelta(hours=9)
                end = start + timedelta(hours=random.choice([8, 9, 9, 10]))
                Shift.objects.create(worker=worker, shop=worker.shop, started_at=start, ended_at=end, created_by=worker)

        # Сканирования за последние 10 дней, с редкими дубликатами и несоответствием устройства.
        ScanEvent.objects.filter(worker__in=all_workers).delete()
        for worker in all_workers:
            shop_products = [p for p in products if p.connection.organization_id == org.id]
            tariff = Tariff.objects.filter(user=worker, pay_type=PayType.PER_UNIT).order_by("-effective_from").first()
            for days_ago in range(9, -1, -1):
                day = today - timedelta(days=days_ago)
                scans_today = random.randint(4, 14)
                for n in range(scans_today):
                    product = random.choice(shop_products)
                    is_dup = n > 0 and random.random() < 0.08
                    is_mismatch = random.random() < 0.05
                    device = devices_by_worker[worker.id] if not is_mismatch else random.choice(list(Device.objects.exclude(assigned_worker=worker)))
                    scan = ScanEvent.objects.create(
                        worker=worker,
                        shop=worker.shop,
                        product=product,
                        device=device,
                        raw_barcode=product.barcode,
                        is_duplicate=is_dup,
                        is_device_mismatch=is_mismatch,
                        unit_rate_snapshot=tariff.rate if tariff else None,
                    )
                    scanned_at = timezone.make_aware(
                        datetime.combine(day, datetime.min.time())
                    ) + timedelta(hours=random.randint(9, 18), minutes=random.randint(0, 59))
                    ScanEvent.objects.filter(pk=scan.pk).update(scanned_at=scanned_at)

        self.stdout.write(self.style.SUCCESS("Демо-данные готовы."))
        self.stdout.write(f"  Владелец:   demo_owner / {DEMO_PASSWORD}")
        self.stdout.write(f"  Менеджеры:  demo_manager1, demo_manager2 / {DEMO_PASSWORD}")
        self.stdout.write(f"  Работники:  demo_worker1..6 / {DEMO_PASSWORD}")

    def _upsert_user(self, username, role, org, shop, first_name, last_name):
        user, _ = CustomUser.objects.get_or_create(
            username=username, defaults={"role": role, "organization": org, "shop": shop}
        )
        user.set_password(DEMO_PASSWORD)
        user.role = role
        user.organization = org
        user.shop = shop
        user.first_name = first_name
        user.last_name = last_name
        user.save()
        return user
