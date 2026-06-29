"""
Django settings for Plate – Meal Tracking API.

All sensitive values are read from environment variables.
Never commit a .env file with real credentials.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

ALLOWED_HOSTS_RAW = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1")
ALLOWED_HOSTS = [h.strip() for h in ALLOWED_HOSTS_RAW.split(",") if h.strip()]

# ---------------------------------------------------------------------------
# Application definition
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    # Third-party
    "rest_framework",
    "django_filters",
    "corsheaders",
    # Local
    "meals",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.common.CommonMiddleware",
    "meals.middleware.RequestLoggingMiddleware",
]

ROOT_URLCONF = "config.urls"

WSGI_APPLICATION = "config.wsgi.application"

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "")

if DATABASE_URL:
    import urllib.parse

    result = urllib.parse.urlparse(DATABASE_URL)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": result.path.lstrip("/"),
            "USER": result.username,
            "PASSWORD": result.password,
            "HOST": result.hostname,
            "PORT": result.port or 5432,
            "OPTIONS": {"sslmode": "require"} if "neon" in (result.hostname or "") else {},
            "CONN_MAX_AGE": 60,
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("POSTGRES_DB", "plate"),
            "USER": os.getenv("POSTGRES_USER", "plate"),
            "PASSWORD": os.getenv("POSTGRES_PASSWORD", "plate"),
            "HOST": os.getenv("POSTGRES_HOST", "db"),
            "PORT": os.getenv("POSTGRES_PORT", "5432"),
            "CONN_MAX_AGE": 60,
        }
    }

# ---------------------------------------------------------------------------
# Internationalisation
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = False
USE_TZ = True

# ---------------------------------------------------------------------------
# REST Framework
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "meals.pagination.MealPageNumberPagination",
    "PAGE_SIZE": 10,
    "DEFAULT_THROTTLE_CLASSES": [],
}

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS_RAW = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173")
CORS_ALLOWED_ORIGINS = [o.strip() for o in CORS_ALLOWED_ORIGINS_RAW.split(",") if o.strip()]
CORS_ALLOW_METHODS = ["DELETE", "GET", "OPTIONS", "POST"]
CORS_ALLOW_HEADERS = ["accept", "authorization", "content-type", "x-requested-with"]

# ---------------------------------------------------------------------------
# App-level config
# ---------------------------------------------------------------------------
DAILY_GOAL_KCAL = int(os.getenv("DAILY_GOAL_KCAL", "2000"))

ALLOWED_TAGS = [
    "vegetarian",
    "non-vegetarian",
    "vegan",
    "high-protein",
    "low-carb",
    "snack",
]

# Duplicate-guard window in minutes (±30 min around eaten_at)
DUPLICATE_WINDOW_MINUTES = 30

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
