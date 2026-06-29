"""URL patterns for the meals application."""

from django.urls import path

from .views import MealDestroyView, MealListCreateView, MealQuickAddView, MealSummaryView, MealTrendsView

urlpatterns = [
    path("meals/", MealListCreateView.as_view(), name="meal-list-create"),
    path("meals/summary/", MealSummaryView.as_view(), name="meal-summary"),
    path("meals/trends/", MealTrendsView.as_view(), name="meal-trends"),
    path("meals/quick-add/", MealQuickAddView.as_view(), name="meal-quick-add"),
    path("meals/<int:pk>/", MealDestroyView.as_view(), name="meal-destroy"),
]
