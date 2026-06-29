"""
Initial migration: creates the Meal table with all fields and indexes.

Indexes added:
  meal_eaten_at_idx   – B-tree on eaten_at for date-range queries
  meal_tags_gin_idx   – GIN on tags for JSONField containment queries

Both are justified in the README.
"""

import django.contrib.postgres.indexes
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Meal",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(db_index=True, max_length=100)),
                ("calories", models.PositiveIntegerField()),
                ("protein_g", models.DecimalField(decimal_places=2, default=0, max_digits=7)),
                ("carbs_g", models.DecimalField(decimal_places=2, default=0, max_digits=7)),
                ("fat_g", models.DecimalField(decimal_places=2, default=0, max_digits=7)),
                ("tags", models.JSONField(blank=True, default=list)),
                ("eaten_at", models.DateTimeField(db_index=True)),
                (
                    "source",
                    models.CharField(
                        choices=[("manual", "Manual"), ("ai", "AI Quick-Add")],
                        default="manual",
                        max_length=10,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "ordering": ["-eaten_at"],
            },
        ),
        migrations.AddIndex(
            model_name="meal",
            index=models.Index(fields=["eaten_at"], name="meal_eaten_at_idx"),
        ),
        migrations.AddIndex(
            model_name="meal",
            index=django.contrib.postgres.indexes.GinIndex(fields=["tags"], name="meal_tags_gin_idx"),
        ),
    ]
