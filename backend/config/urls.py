"""Root URL configuration for Plate API."""

from django.urls import include, path

urlpatterns = [
    path("api/", include("meals.urls")),
]
