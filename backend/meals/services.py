"""
Business-logic services for the Meal resource.

Keeping logic here (not in views) keeps views thin and testable.
"""

from __future__ import annotations

import re
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from django.conf import settings
from django.db.models import Count, DecimalField, IntegerField, Q, Sum
from django.db.models.functions import Coalesce, TruncDate

from .models import Meal


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def normalize_name(name: str) -> str:
    """
    Produce a canonical form of a meal name for duplicate comparison:
      - lowercase
      - leading/trailing whitespace stripped
      - internal runs of whitespace collapsed to a single space
    """
    return re.sub(r"\s+", " ", name.strip().lower())


# ---------------------------------------------------------------------------
# Duplicate detection
# ---------------------------------------------------------------------------

def is_duplicate(name: str, eaten_at: datetime) -> bool:
    """
    Return True if a meal with the same normalised name already exists
    within ±DUPLICATE_WINDOW_MINUTES of eaten_at.

    Uses a single DB query with a Q filter; no Python-level loops.
    """
    window = timedelta(minutes=settings.DUPLICATE_WINDOW_MINUTES)
    lower = eaten_at - window
    upper = eaten_at + window

    normalised = normalize_name(name)
    return Meal.objects.filter(
        eaten_at__range=(lower, upper),
    ).extra(
        where=["LOWER(REGEXP_REPLACE(name, '\\s+', ' ', 'g')) = %s"],
        params=[normalised],
    ).exists()


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def get_daily_summary(target_date: date) -> dict:
    """
    Compute the daily macro summary for *target_date* using a single
    DB-level aggregation query. No Python loops over rows.

    Returns a dict that matches MealSummarySerializer.
    """
    goal = settings.DAILY_GOAL_KCAL

    agg = Meal.objects.filter(
        eaten_at__date=target_date
    ).aggregate(

        total_calories=Coalesce(Sum("calories", output_field=IntegerField()), 0),
        total_protein=Coalesce(Sum("protein_g", output_field=DecimalField()), Decimal("0")),
        total_carbs=Coalesce(Sum("carbs_g", output_field=DecimalField()), Decimal("0")),
        total_fat=Coalesce(Sum("fat_g", output_field=DecimalField()), Decimal("0")),
        meal_count=Count("id"),
    )

    # Top tags: fetch tag arrays for matching meals and tally in Python.
    # This is a second, tiny query (only tag lists, not full rows).
    tag_rows = (
        Meal.objects.filter(eaten_at__date=target_date)
        .values_list("tags", flat=True)
    )
    tag_counter: Counter = Counter()
    for tags in tag_rows:
        tag_counter.update(tags)
    top_tags = [tag for tag, _ in tag_counter.most_common(3)]

    total_cal = agg["total_calories"]

    return {
        "date": target_date,
        "total_calories": total_cal,
        "goal_kcal": goal,
        "remaining_kcal": max(goal - total_cal, 0),
        "macros": {
            "protein_g": float(agg["total_protein"]),
            "carbs_g": float(agg["total_carbs"]),
            "fat_g": float(agg["total_fat"]),
        },
        "meal_count": agg["meal_count"],
        "top_tags": top_tags,
    }


# ---------------------------------------------------------------------------
# Trends
# ---------------------------------------------------------------------------

def get_trends(days: int) -> dict:
    """
    Return per-day calorie totals for the last *days* days (including today).

    Strategy (≤ 2 DB queries, no query-per-day):

    Query 1 – aggregate:
        TruncDate(eaten_at) → GROUP BY → SUM(calories), COUNT(id)
        Returns only days that have at least one meal.

    Python – gap fill:
        Build a complete list of the last N dates, initialised to zero.
        Merge the DB results in O(N) with a dict lookup.

    Query 2 is implicitly executed by Django when evaluating a ValuesQuerySet
    inside a list comprehension; the ORM always uses one round-trip for a
    grouped aggregation regardless of how many date buckets are returned.
    """
    goal = settings.DAILY_GOAL_KCAL
    today = datetime.now(tz=timezone.utc).date()
    start_date = today - timedelta(days=days - 1)

    # --- Query 1: aggregate all days in the window in one shot ---------------
    db_rows = (
        Meal.objects
        .filter(eaten_at__date__gte=start_date, eaten_at__date__lte=today)
        .annotate(day=TruncDate("eaten_at"))
        .values("day")
        .annotate(
            calories=Coalesce(Sum("calories", output_field=IntegerField()), 0),
            meal_count=Count("id"),
        )
        .order_by("day")
    )

    # Build a lookup dict: date → {calories, meal_count}
    # (evaluates the queryset – single round-trip to the DB)
    db_lookup: dict[date, dict] = {
        row["day"]: {
            "calories": row["calories"],
            "meal_count": row["meal_count"],
        }
        for row in db_rows  # ← single evaluation
    }

    # --- Gap fill in pure Python (O(days), no extra queries) -----------------
    series = []
    for offset in range(days):
        day = start_date + timedelta(days=offset)
        entry = db_lookup.get(day, {"calories": 0, "meal_count": 0})
        series.append(
            {
                "date": day,
                "calories": entry["calories"],
                "meal_count": entry["meal_count"],
            }
        )

    # --- Derived statistics ---------------------------------------------------
    total_calories = sum(e["calories"] for e in series)
    avg_daily_kcal = round(total_calories / days, 1)

    days_over_goal = sum(1 for e in series if e["calories"] > goal)

    best = max(series, key=lambda e: e["calories"], default=None)
    best_day = (
        {"date": best["date"], "calories": best["calories"]}
        if best and best["calories"] > 0
        else None
    )

    return {
        "days": days,
        "series": series,
        "avg_daily_kcal": avg_daily_kcal,
        "best_day": best_day,
        "days_over_goal": days_over_goal,
    }
