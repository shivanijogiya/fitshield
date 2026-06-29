"""
Views for the Meal resource.

Each view is intentionally thin: it delegates validation to serializers
and business logic to services.py.  Views are responsible only for:
  - Routing request data to the right service
  - Selecting the correct HTTP status code
  - Returning the serialized response
"""

from __future__ import annotations

from datetime import date, datetime, timezone

from django.conf import settings
from rest_framework import status
from rest_framework.generics import DestroyAPIView, ListCreateAPIView, RetrieveDestroyAPIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .filters import MealFilterSet
from .models import Meal
from .pagination import MealPageNumberPagination
from .serializers import MealSerializer, MealSummarySerializer, TrendsSerializer
from .quick_add import QuickAddError, QuickAddParseError, parse_meals_from_text
from .services import get_daily_summary, get_trends, is_duplicate


# ---------------------------------------------------------------------------
# POST /api/meals/  &  GET /api/meals/
# ---------------------------------------------------------------------------

class MealListCreateView(ListCreateAPIView):
    """
    GET  – List meals with optional filters (date, tag, search) and pagination.
    POST – Create a new meal with full validation and duplicate guard.
    """

    serializer_class = MealSerializer
    pagination_class = MealPageNumberPagination
    filterset_class = MealFilterSet

    def get_queryset(self):
        """Return all meals ordered by eaten_at descending."""
        return Meal.objects.all()

    def create(self, request: Request, *args, **kwargs) -> Response:
        """
        Create a meal.

        Returns 409 if a meal with the same normalised name exists within
        ±30 minutes of the supplied eaten_at.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        name: str = serializer.validated_data["name"]
        eaten_at: datetime = serializer.validated_data["eaten_at"]

        if is_duplicate(name, eaten_at):
            return Response(
                {
                    "detail": (
                        "A meal with the same name already exists within "
                        f"±{settings.DUPLICATE_WINDOW_MINUTES} minutes of the "
                        "supplied eaten_at time."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        meal = serializer.save()
        return Response(
            MealSerializer(meal).data,
            status=status.HTTP_201_CREATED,
        )


# ---------------------------------------------------------------------------
# DELETE /api/meals/{id}/
# ---------------------------------------------------------------------------

class MealDestroyView(DestroyAPIView):
    """
    DELETE /api/meals/{id}/

    Returns 204 on success, 404 if the meal does not exist.
    """

    serializer_class = MealSerializer
    queryset = Meal.objects.all()


# ---------------------------------------------------------------------------
# GET /api/meals/summary/
# ---------------------------------------------------------------------------

class MealSummaryView(APIView):
    """
    GET /api/meals/summary/?date=YYYY-MM-DD

    Returns the daily macro summary computed entirely in the database via
    a single aggregation query. Falls back to today if ?date is omitted.
    """

    def get(self, request: Request, *args, **kwargs) -> Response:
        date_param = request.query_params.get("date")

        if date_param:
            try:
                target_date = date.fromisoformat(date_param)
            except ValueError:
                return Response(
                    {"date": "Invalid date format. Use YYYY-MM-DD."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            target_date = datetime.now(tz=timezone.utc).date()

        data = get_daily_summary(target_date)
        serializer = MealSummarySerializer(data)
        return Response(serializer.data)


# ---------------------------------------------------------------------------
# GET /api/meals/trends/
# ---------------------------------------------------------------------------

class MealTrendsView(APIView):
    """
    GET /api/meals/trends/?days=7

    Returns per-day calorie totals for the last N days, gap-filled so that
    days with no meals still appear with zeros.

    Constraints:
      - days defaults to 7
      - days max 30
      - values outside [1, 30] return 400
      - implemented with at most 2 DB queries regardless of N
    """

    DAYS_DEFAULT = 7
    DAYS_MAX = 30

    def get(self, request: Request, *args, **kwargs) -> Response:
        raw = request.query_params.get("days", str(self.DAYS_DEFAULT))

        try:
            days = int(raw)
        except (TypeError, ValueError):
            return Response(
                {"days": "Must be an integer."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not (1 <= days <= self.DAYS_MAX):
            return Response(
                {"days": f"Must be between 1 and {self.DAYS_MAX}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = get_trends(days)
        serializer = TrendsSerializer(data)
        return Response(serializer.data)


# ---------------------------------------------------------------------------
# POST /api/meals/quick-add/
# ---------------------------------------------------------------------------

class MealQuickAddView(APIView):
    """
    POST /api/meals/quick-add/

    Accepts free-text describing one or more meals and uses an LLM (Groq
    llama3) to parse them into structured entries which are saved to the DB.

    Request body:
        { "text": "2 rotis, dal makhani and one lassi" }

    Response 201:
        { "created": [ ...meal objects... ] }

    Errors:
        400 – text field missing or blank
        422 – LLM output could not be parsed into valid meal data
        503 – Groq API unreachable
    """

    def post(self, request: Request, *args, **kwargs) -> Response:
        text = request.data.get("text", "").strip()
        if not text:
            return Response(
                {"text": "This field is required and cannot be blank."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            meal_dicts = parse_meals_from_text(text)
        except QuickAddParseError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        except QuickAddError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        from django.utils.timezone import now as django_now

        created_meals = []
        for item in meal_dicts:
            serializer = MealSerializer(
                data={
                    "name": item.get("name", "Unknown"),
                    "calories": item.get("calories", 1),
                    "protein_g": item.get("protein_g", 0),
                    "carbs_g": item.get("carbs_g", 0),
                    "fat_g": item.get("fat_g", 0),
                    "tags": item.get("tags", []),
                    "eaten_at": django_now().isoformat(),
                    "source": Meal.SOURCE_AI,
                }
            )
            if serializer.is_valid():
                meal = serializer.save()
                created_meals.append(MealSerializer(meal).data)

        return Response(
            {"created": created_meals},
            status=status.HTTP_201_CREATED,
        )
