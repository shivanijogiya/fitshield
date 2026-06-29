"""
RequestLoggingMiddleware
========================

Logs one structured line per HTTP request to stdout (captured by Docker /
Render log streams).

Format:
    [2026-06-12 13:30:01 UTC] POST /api/meals/ → 201 in 28ms

Placement in MIDDLEWARE:
    After CorsMiddleware and SecurityMiddleware so CORS pre-flights are
    still logged, but before DRF views so the timer covers full request
    processing.
"""

from __future__ import annotations

import logging
import time

logger = logging.getLogger("plate.requests")


class RequestLoggingMiddleware:
    """WSGI middleware that times every request and logs a summary line."""

    def __init__(self, get_response) -> None:
        self.get_response = get_response

    def __call__(self, request):
        start = time.monotonic()

        response = self.get_response(request)

        duration_ms = round((time.monotonic() - start) * 1000)

        logger.info(
            "%s %s → %s in %dms",
            request.method,
            request.get_full_path(),
            response.status_code,
            duration_ms,
        )

        return response


# ---------------------------------------------------------------------------
# Logging configuration (applied at import time so it works without a full
# Django logging dict when the module is imported directly in tests).
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s UTC] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
