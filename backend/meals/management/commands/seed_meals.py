"""
Management command: seed_meals
==============================

Loads seed_meals.json into the database only when the Meal table is empty.
Safe to call on every container start-up; idempotent.

Usage:
    python manage.py seed_meals
    python manage.py seed_meals --force   # clear existing data first
"""

from __future__ import annotations

import json
from pathlib import Path

from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime

from meals.models import Meal


# Try multiple locations
_base = Path(__file__).resolve()
SEED_FILE = _base.parents[4] / "seed_meals.json"
if not SEED_FILE.exists():
    SEED_FILE = _base.parents[3] / "seed_meals.json"
if not SEED_FILE.exists():
    SEED_FILE = Path("/app/seed_meals.json")


class Command(BaseCommand):
    help = "Seed the database with sample meals from seed_meals.json."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--force",
            action="store_true",
            help="Delete all existing meals before seeding.",
        )

    def handle(self, *args, **options) -> None:
        if options["force"]:
            deleted, _ = Meal.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Deleted {deleted} existing meal(s)."))

        if Meal.objects.exists():
            self.stdout.write(self.style.SUCCESS("Database already seeded – skipping."))
            return

        if not SEED_FILE.exists():
            self.stderr.write(
                self.style.ERROR(f"Seed file not found: {SEED_FILE}")
            )
            return

        raw = SEED_FILE.read_text(encoding="utf-8")
        meals_data: list[dict] = json.loads(raw)

        created = 0
        for item in meals_data:
            Meal.objects.create(
                name=item["name"],
                calories=item["calories"],
                protein_g=item.get("protein_g", 0),
                carbs_g=item.get("carbs_g", 0),
                fat_g=item.get("fat_g", 0),
                tags=item.get("tags", []),
                eaten_at=parse_datetime(item["eaten_at"]),
                source=item.get("source", Meal.SOURCE_MANUAL),
            )
            created += 1

        self.stdout.write(self.style.SUCCESS(f"Seeded {created} meal(s) successfully."))
