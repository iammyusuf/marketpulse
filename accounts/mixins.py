class RoleScopedQuerysetMixin:
    """
    Подмешивается к viewset'ам, где видимость записей зависит от роли:
    owner — вся организация, manager — только свой склад, worker — только свои записи.

    Наследник задаёт `org_lookup`/`shop_lookup`/`worker_lookup` — ORM-путь от модели
    до Organization/Shop/CustomUser соответственно — и может переопределить
    `worker_queryset()`, если работнику вообще не положено видеть эти записи.
    """

    org_lookup = "organization"
    shop_lookup = "shop"
    worker_lookup = "worker"

    def scope_by_role(self, queryset):
        user = self.request.user
        if user.is_owner:
            return queryset.filter(**{self.org_lookup: user.organization})
        if user.is_manager:
            return queryset.filter(**{self.shop_lookup: user.shop})
        return self.worker_queryset(queryset, user)

    def worker_queryset(self, queryset, user):
        return queryset.filter(**{self.worker_lookup: user})
