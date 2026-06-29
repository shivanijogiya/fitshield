"""
FilterSet for the Meal list endpoint.

Supports:
  ?date=YYYY-MM-DD   – filter by calendar date of eaten_at
  ?tag=vegetarian    – filter by tag containment (uses GIN index)
  ?search=paneer     – case-insensitive name substring match

All filters are combinable in a single request.
"""

from __future__ import annotations

import django_filters
from django.db.models import QuerySet

from .models import Meal


class MealFilterSet(django_filters.FilterSet):
    """
    Custom FilterSet to handle the specialised date and tag lookups that
    cannot be expressed with the default field-to-lookup mapping alone.
    """

    date = django_filters.DateFilter(method="filter_by_date")
    tag = django_filters.CharFilter(method="filter_by_tag")
    search = django_filters.CharFilter(method="filter_by_search")

    class Meta:
        model = Meal
        fields: list = []  # all lookups handled via custom methods

    # ------------------------------------------------------------------
    # Custom filter methods
    # ------------------------------------------------------------------

    def filter_by_date(self, queryset: QuerySet, name: str, value) -> QuerySet:
        """Filter to meals whose eaten_at falls on *value* (a date object)."""
        return queryset.filter(eaten_at__date=value)

    def filter_by_tag(self, queryset: QuerySet, name: str, value: str) -> QuerySet:
        """
        Filter to meals that contain *value* in their tags array.

        Uses PostgreSQL's JSONField containment operator (@>) which is
        accelerated by the GIN index on the tags column.
        """
        return queryset.filter(tags__contains=[value])

    def filter_by_search(self, queryset: QuerySet, name: str, value: str) -> QuerySet:
        """Case-insensitive substring match on the meal name."""
        return queryset.filter(name__icontains=value)
