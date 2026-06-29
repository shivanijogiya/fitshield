"""
Meal model – the single source of truth for logged food entries.

Field notes
-----------
name        : Human-readable label (max 100 chars, indexed for search).
calories    : Energy in kcal (1–5 000).
protein_g   : Protein in grams (≥ 0).
carbs_g     : Carbohydrates in grams (≥ 0).
fat_g       : Fat in grams (≥ 0).
tags        : JSONField storing a list of validated tag strings.
              Indexed for fast tag-based filtering.
eaten_at    : UTC datetime of consumption.
              Indexed for date-range queries (daily summary, trends).
source      : 'manual' or 'ai' – tracks how the entry was created.
"""

from django.contrib.postgres.indexes import GinIndex
from django.db import models


class Meal(models.Model):
    """A single meal or food item logged by the user."""

    SOURCE_MANUAL = "manual"
    SOURCE_AI = "ai"
    SOURCE_CHOICES = [
        (SOURCE_MANUAL, "Manual"),
        (SOURCE_AI, "AI Quick-Add"),
    ]

    name = models.CharField(max_length=100, db_index=True)
    calories = models.PositiveIntegerField()
    protein_g = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    carbs_g = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    fat_g = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    tags = models.JSONField(default=list, blank=True)
    eaten_at = models.DateTimeField(db_index=True)
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES, default=SOURCE_MANUAL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-eaten_at"]
        indexes = [
            # Fast lookup by calendar date (used by summary and list-by-date filters).
            # PostgreSQL can use this index for WHERE DATE(eaten_at) = '...' after
            # casting, but a plain B-tree on eaten_at covers range queries even better.
            models.Index(fields=["eaten_at"], name="meal_eaten_at_idx"),
            # GIN index allows efficient containment queries on the JSONField tags array,
            # e.g. WHERE tags @> '["vegetarian"]'::jsonb
            GinIndex(fields=["tags"], name="meal_tags_gin_idx"),
        ]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.name} ({self.calories} kcal) @ {self.eaten_at:%Y-%m-%d %H:%M}"
