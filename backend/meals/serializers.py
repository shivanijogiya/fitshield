"""
Serializers for the Meal resource.

Validation rules (all enforced at this layer, never in views):
  - name: required, max 100 chars, cannot be blank after stripping whitespace
  - calories: required integer, 1 – 5 000 inclusive
  - protein_g / carbs_g / fat_g: optional, must be ≥ 0
  - tags: list of strings, each must be from the ALLOWED_TAGS set
  - eaten_at: must not be in the future (UTC)

Duplicate detection lives in services.py; the serializer does not handle it
because 409 is a business-level concern rather than a field-level error.
"""

from __future__ import annotations

from datetime import datetime, timezone

from django.conf import settings
from rest_framework import serializers

from .models import Meal


class MealSerializer(serializers.ModelSerializer):
    """Full read/write serializer for a Meal instance."""

    class Meta:
        model = Meal
        fields = [
            "id",
            "name",
            "calories",
            "protein_g",
            "carbs_g",
            "fat_g",
            "tags",
            "eaten_at",
            "source",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    # ------------------------------------------------------------------
    # Field-level validators
    # ------------------------------------------------------------------

    def validate_name(self, value: str) -> str:
        """Name must not be blank (after stripping) and max 100 chars."""
        stripped = value.strip()
        if not stripped:
            raise serializers.ValidationError("Name cannot be blank.")
        if len(stripped) > 100:
            raise serializers.ValidationError("Name cannot exceed 100 characters.")
        return stripped

    def validate_calories(self, value: int) -> int:
        """Calories must be between 1 and 5 000 kcal."""
        if not (1 <= value <= 5000):
            raise serializers.ValidationError("Must be between 1 and 5 000 kcal.")
        return value

    def validate_protein_g(self, value) -> float:
        if value < 0:
            raise serializers.ValidationError("Must be 0 or greater.")
        return value

    def validate_carbs_g(self, value) -> float:
        if value < 0:
            raise serializers.ValidationError("Must be 0 or greater.")
        return value

    def validate_fat_g(self, value) -> float:
        if value < 0:
            raise serializers.ValidationError("Must be 0 or greater.")
        return value

    def validate_tags(self, value: list) -> list:
        """Every tag must belong to the fixed allowed set."""
        if not isinstance(value, list):
            raise serializers.ValidationError("Tags must be a list.")
        allowed = set(settings.ALLOWED_TAGS)
        invalid = [t for t in value if t not in allowed]
        if invalid:
            raise serializers.ValidationError(
                f"Invalid tag(s): {invalid}. "
                f"Allowed values: {sorted(allowed)}."
            )
        return value

    def validate_eaten_at(self, value: datetime) -> datetime:
        """eaten_at must not be in the future."""
        now = datetime.now(tz=timezone.utc)
        if value > now:
            raise serializers.ValidationError("eaten_at cannot be in the future.")
        return value


class MealSummarySerializer(serializers.Serializer):
    """Read-only serializer for the /summary/ endpoint response."""

    date = serializers.DateField()
    total_calories = serializers.IntegerField()
    goal_kcal = serializers.IntegerField()
    remaining_kcal = serializers.IntegerField()
    macros = serializers.DictField()
    meal_count = serializers.IntegerField()
    top_tags = serializers.ListField(child=serializers.CharField())


class TrendsDaySerializer(serializers.Serializer):
    """A single day's entry in the trends series."""

    date = serializers.DateField()
    calories = serializers.IntegerField()
    meal_count = serializers.IntegerField()


class TrendsSerializer(serializers.Serializer):
    """Read-only serializer for the /trends/ endpoint response."""

    days = serializers.IntegerField()
    series = TrendsDaySerializer(many=True)
    avg_daily_kcal = serializers.FloatField()
    best_day = serializers.DictField(allow_null=True)
    days_over_goal = serializers.IntegerField()
