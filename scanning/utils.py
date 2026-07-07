from datetime import date, timedelta

from django.utils import timezone


def resolve_period(period: str) -> tuple[date, date]:
    """Возвращает (start, end) дат для сводки продуктивности по строковому периоду."""
    today = timezone.localdate()
    if period == "day":
        return today, today
    if period == "week":
        return today - timedelta(days=today.weekday()), today
    if period == "month":
        return today.replace(day=1), today
    raise ValueError(f"Неизвестный период: {period}")
