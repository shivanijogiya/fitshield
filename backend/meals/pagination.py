"""
Custom pagination for the Meal list endpoint.

Enforces page_size=10 server-side so that a large dataset never returns
all rows in a single response. The client receives:

    {
        "count": 58,
        "next": "https://api.example.com/api/meals/?page=3",
        "previous": "https://api.example.com/api/meals/?page=1",
        "results": [ ... ]
    }
"""

from rest_framework.pagination import PageNumberPagination


class MealPageNumberPagination(PageNumberPagination):
    """Page-number pagination locked to 10 results per page."""

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100
