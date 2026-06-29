# Plate — Meal Tracking API & Dashboard

A production-quality meal tracking system built for the Fitshield Dietfood Full-Stack Developer Assessment. Users log food entries during the day; the system tracks calories and macros against a configurable daily goal and exposes a React dashboard with live updates, filtering, and a 7-day trend chart.

---

## Project Overview

**Plate** is a mini nutrition-tracking module. The backend is a Django REST API backed by PostgreSQL. The frontend is a React single-page application that talks to the live API. Everything runs locally via a single `docker compose up` command.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 5 · Django REST Framework · django-filter |
| Database | PostgreSQL 16 (Neon for cloud) |
| Frontend | React 18 · Vite · Axios |
| Containerisation | Docker · Docker Compose |
| Backend deployment | Render |
| Frontend deployment | Vercel |

---

## Architecture

```
meal-tracker/
├── backend/
│   ├── config/          # Django project settings, root URLs, WSGI
│   ├── meals/
│   │   ├── models.py        # Meal model + DB indexes
│   │   ├── serializers.py   # Input validation (all rules here, never in views)
│   │   ├── views.py         # Thin views — delegate to services
│   │   ├── services.py      # Business logic: summary aggregation, trends, duplicate guard
│   │   ├── filters.py       # django-filter FilterSet (date, tag, search)
│   │   ├── pagination.py    # Page-number pagination (page_size=10)
│   │   ├── middleware.py    # Request logging middleware
│   │   └── management/commands/seed_meals.py
│   ├── entrypoint.sh    # migrate → seed → gunicorn
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── services/api.js      # Axios instance, all API calls centralised
│   │   ├── hooks/useMeals.js    # All state & side-effects in one hook
│   │   ├── components/
│   │   │   ├── AddMealForm.jsx  # Inline-validated form
│   │   │   ├── MealList.jsx     # Paginated cards with delete
│   │   │   ├── SummaryBar.jsx   # Progress bar + macro chips
│   │   │   ├── FilterBar.jsx    # Date/tag/search controls
│   │   │   └── TrendsChart.jsx  # Hand-rolled SVG bar chart
│   │   ├── styles/global.css    # Single CSS file, CSS variables, no framework
│   │   └── App.jsx
│   ├── Dockerfile
│   └── nginx.conf
├── seed_meals.json
└── docker-compose.yml
```

**Key design principle:** Views are intentionally thin. All business logic lives in `services.py`. All validation lives in `serializers.py`. This makes both independently testable without spinning up Django.

---

## Folder Structure

```
config/          Django project package (settings, root urls, wsgi)
meals/           The only Django app — contains every feature
  migrations/    Auto-generated + manually reviewed DB migrations
  management/    Custom manage.py commands (seed_meals)
frontend/src/
  components/    Presentational components; receive data via props
  hooks/         useMeals — the single source of truth for all state
  services/      api.js — Axios instance + typed fetch functions
  styles/        global.css — single stylesheet with CSS custom properties
```

---

## Setup Instructions

### Prerequisites

- Docker ≥ 24 and Docker Compose v2

### 1. Clone the repo

```bash
git clone <your-repo-url>
cd meal-tracker
```

### 2. Copy environment file

```bash
cp backend/.env.example backend/.env
```

The defaults work as-is for local Docker development. No editing required.

### 3. Start everything

```bash
docker compose up --build
```

That single command:
1. Starts PostgreSQL and waits for it to be healthy.
2. Runs `python manage.py migrate`.
3. Runs `python manage.py seed_meals` (idempotent — skips if data exists).
4. Starts Gunicorn on port 8000.
5. Builds and serves the React app via Nginx on port 5173.

### Access

| Service | URL |
|---------|-----|
| API | http://localhost:8000/api/ |
| Frontend | http://localhost:5173 |

---

## Docker Instructions

```bash
# Start all services
docker compose up

# Rebuild after code changes
docker compose up --build

# Run in background
docker compose up -d

# View logs
docker compose logs -f backend

# Stop
docker compose down

# Destroy volumes (wipes the database)
docker compose down -v
```

---

## Local Development (without Docker)

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # set DATABASE_URL to a local Postgres instance
python manage.py migrate
python manage.py seed_meals
python manage.py runserver

# Frontend (separate terminal)
cd frontend
npm install
cp .env.example .env          # set VITE_API_BASE_URL=http://localhost:8000
npm run dev
```

---

## Environment Variables

### Backend

| Variable | Purpose | Example |
|----------|---------|---------|
| `SECRET_KEY` | Django secret key | `django-insecure-...` |
| `DEBUG` | Enable debug mode | `False` |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts | `localhost,api.example.com` |
| `DATABASE_URL` | Full Postgres URL (Neon/Render) | `postgresql://user:pass@host/db` |
| `POSTGRES_DB` | DB name (local Docker) | `plate` |
| `POSTGRES_USER` | DB user (local Docker) | `plate` |
| `POSTGRES_PASSWORD` | DB password (local Docker) | `plate` |
| `POSTGRES_HOST` | DB host (local Docker) | `db` |
| `DAILY_GOAL_KCAL` | Daily calorie target | `2000` |
| `CORS_ALLOWED_ORIGINS` | Comma-separated allowed origins | `https://plate.vercel.app` |

### Frontend

| Variable | Purpose | Example |
|----------|---------|---------|
| `VITE_API_BASE_URL` | Backend API base URL (no trailing slash) | `https://plate-api.onrender.com` |

---

## Database Schema

### Meal

| Field | Type | Notes |
|-------|------|-------|
| `id` | `bigint` PK | Auto-increment |
| `name` | `varchar(100)` | Indexed for name search; normalised for duplicate guard |
| `calories` | `integer` | 1–5 000 kcal, validated in serializer |
| `protein_g` | `decimal(7,2)` | ≥ 0 |
| `carbs_g` | `decimal(7,2)` | ≥ 0 |
| `fat_g` | `decimal(7,2)` | ≥ 0 |
| `tags` | `jsonb` | Array of strings from a fixed allowed set; GIN-indexed |
| `eaten_at` | `timestamptz` | UTC; must not be in the future; B-tree indexed |
| `source` | `varchar(10)` | `'manual'` or `'ai'` (bonus field) |
| `created_at` | `timestamptz` | Auto-set on insert; not exposed to client filters |

All timestamps are stored in UTC and returned in ISO 8601 format.

---

## API Documentation

Base path: `/api/`

### POST /api/meals/ — Create a meal

**Purpose:** Log a new food entry.

**Request body:**
```json
{
  "name": "Paneer Tikka",
  "calories": 320,
  "protein_g": 24,
  "carbs_g": 12,
  "fat_g": 18,
  "tags": ["vegetarian", "high-protein"],
  "eaten_at": "2026-06-12T13:30:00Z"
}
```

**Response 201:**
```json
{
  "id": 1,
  "name": "Paneer Tikka",
  "calories": 320,
  "protein_g": "24.00",
  "carbs_g": "12.00",
  "fat_g": "18.00",
  "tags": ["vegetarian", "high-protein"],
  "eaten_at": "2026-06-12T13:30:00Z",
  "source": "manual",
  "created_at": "2026-06-12T08:00:00Z"
}
```

**Errors:**

| Code | Reason |
|------|--------|
| 400 | Validation failure — response contains per-field errors |
| 409 | Duplicate detected — same normalised name within ±30 min |

**Validation rules:**
- `name`: required, max 100 chars, stripped of leading/trailing whitespace
- `calories`: required integer, 1–5 000 inclusive
- `protein_g / carbs_g / fat_g`: optional, must be ≥ 0
- `tags`: each element must be one of `vegetarian | non-vegetarian | vegan | high-protein | low-carb | snack`
- `eaten_at`: required, must not be in the future (UTC)

**Sample 400 response:**
```json
{
  "name": ["Name cannot be blank."],
  "calories": ["Must be between 1 and 5 000 kcal."],
  "tags": ["Invalid tag(s): ['junk']. Allowed values: ['high-protein', 'low-carb', 'non-vegetarian', 'snack', 'vegan', 'vegetarian']."]
}
```

---

### GET /api/meals/ — List meals

**Purpose:** Paginated meal list with combinable filters.

**Query parameters:**

| Param | Type | Description |
|-------|------|-------------|
| `date` | `YYYY-MM-DD` | Filter by calendar date of `eaten_at` |
| `tag` | string | Filter by tag membership |
| `search` | string | Case-insensitive substring match on `name` |
| `page` | integer | Page number (default 1) |

**All filters combine with AND logic.** Example: `?date=2026-06-12&tag=vegetarian&search=paneer`

**Response 200:**
```json
{
  "count": 58,
  "next": "http://localhost:8000/api/meals/?page=2",
  "previous": null,
  "results": [ ... ]
}
```

---

### GET /api/meals/summary/?date=YYYY-MM-DD — Daily summary

**Purpose:** Aggregated dashboard payload computed entirely in the database.

**Query parameters:**

| Param | Type | Description |
|-------|------|-------------|
| `date` | `YYYY-MM-DD` | Target date (defaults to today UTC) |

**Response 200:**
```json
{
  "date": "2026-06-12",
  "total_calories": 1540,
  "goal_kcal": 2000,
  "remaining_kcal": 460,
  "macros": {
    "protein_g": 92.0,
    "carbs_g": 160.0,
    "fat_g": 54.0
  },
  "meal_count": 4,
  "top_tags": ["vegetarian", "high-protein"]
}
```

---

### DELETE /api/meals/{id}/ — Delete a meal

**Purpose:** Remove a logged meal entry.

**Response:** `204 No Content`

**Error:** `404 Not Found` if meal does not exist.

---

### GET /api/meals/trends/?days=7 — Calorie trend series

**Purpose:** Per-day calorie totals for the last N days, gap-filled.

**Query parameters:**

| Param | Type | Default | Max |
|-------|------|---------|-----|
| `days` | integer | 7 | 30 |

**Response 200:**
```json
{
  "days": 7,
  "series": [
    { "date": "2026-06-06", "calories": 1820, "meal_count": 4 },
    { "date": "2026-06-07", "calories": 0,    "meal_count": 0 },
    { "date": "2026-06-08", "calories": 2140, "meal_count": 5 }
  ],
  "avg_daily_kcal": 1320.0,
  "best_day": { "date": "2026-06-08", "calories": 2140 },
  "days_over_goal": 1
}
```

**Error 400** when `days` is outside [1, 30]:
```json
{ "days": "Must be between 1 and 30." }
```

---

## Pagination

`MealPageNumberPagination` enforces `page_size = 10` server-side. Even a database with 100 000 rows returns exactly 10 per request. The client receives `count`, `next`, and `previous` to navigate pages.

```python
class MealPageNumberPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100
```

---

## Filtering

`MealFilterSet` in `filters.py` uses `django-filter`. Three custom methods:

```python
def filter_by_date(self, qs, name, value):
    return qs.filter(eaten_at__date=value)           # uses B-tree index

def filter_by_tag(self, qs, name, value):
    return qs.filter(tags__contains=[value])          # uses GIN index

def filter_by_search(self, qs, name, value):
    return qs.filter(name__icontains=value)           # uses name index
```

All three filters compose with AND logic when combined in a single request.

---

## Summary Aggregation

The `/summary/` endpoint computes all statistics in **one SQL round-trip** using Django's `aggregate()`:

```python
agg = Meal.objects.filter(
    eaten_at__date=target_date
).aggregate(
    total_calories=Coalesce(Sum("calories", output_field=IntegerField()), 0),
    total_protein=Coalesce(Sum("protein_g",  output_field=DecimalField()), 0),
    total_carbs=  Coalesce(Sum("carbs_g",    output_field=DecimalField()), 0),
    total_fat=    Coalesce(Sum("fat_g",      output_field=DecimalField()), 0),
    meal_count=Count("id"),
)
```

**Why database aggregation, not a Python loop?**

| Approach | 1 000 meals | 100 000 meals |
|----------|-------------|---------------|
| Python loop | transfers all rows over the wire, O(n) Python | memory spike + slow |
| `aggregate()` | transfers 1 row (5 scalars) | identical performance |

PostgreSQL executes the `SUM` with a single sequential scan of the filtered partition (or an index scan if the selectivity is high). The ORM never materialises individual rows.

---

## Trends Endpoint

### Gap filling

PostgreSQL can only return rows that exist. On a day with zero meals, there is no row — the DB cannot return a zero for it. The gap-filling algorithm:

1. **Query 1:** `TruncDate("eaten_at") → GROUP BY → SUM, COUNT` over the date window. Returns only days with data.
2. **Python dict:** convert results to `{date: {calories, meal_count}}`.
3. **Python loop over N dates:** for each day in the window, look up from the dict; use `{calories:0, meal_count:0}` if absent.

This is always **exactly 2 DB queries** regardless of N (QuerySet lazy evaluation means the grouped aggregate is one round-trip; the top-tag query in summary is separate).

### Average calculation

`avg_daily_kcal` averages over **all N days including empty ones**. This produces a conservative, honest average — it does not inflate the figure by ignoring rest days. This matches the assessment spec: "averages over all N days including empty ones."

### Performance & complexity

- Time complexity: O(M log M) where M = meals in the window (PostgreSQL sort for GROUP BY).
- Python gap-fill: O(N) where N ≤ 30.
- No query-per-day, no N+1, no Python-level aggregation of meal rows.

---

## Validation Strategy

All validation is co-located in `MealSerializer`. Per-field validator methods (`validate_<field>`) raise `serializers.ValidationError` with a human-readable message when a rule is violated. DRF collects all field errors and returns them in a single 400 response keyed by field name:

```json
{
  "name":     ["Name cannot be blank."],
  "calories": ["Must be between 1 and 5 000 kcal."],
  "eaten_at": ["eaten_at cannot be in the future."]
}
```

No generic "invalid input" messages — every error names the exact field and reason.

---

## Duplicate Detection

### Normalisation

Before comparing names, the service applies:
```python
def normalize_name(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip().lower())
```
`"Paneer Tikka"`, `"paneer tikka"`, and `" PANEER  TIKKA "` all map to `"paneer tikka"`.

### Time window

The guard checks whether a meal with the same normalised name exists within ±30 minutes of `eaten_at`. This window is configurable via `DUPLICATE_WINDOW_MINUTES` in `settings.py`.

### Why HTTP 409?

`409 Conflict` is the semantically correct status for "the request could not be completed because of a conflict with the current state of the target resource." A duplicate meal is a resource conflict, not a malformed request (400) or a server error (500). The client can distinguish it and show a meaningful message.

---

## Database Indexes

### `meal_eaten_at_idx` — B-tree on `eaten_at`

```sql
CREATE INDEX meal_eaten_at_idx ON meals_meal (eaten_at);
```

**Justification:** Every date-scoped query (`/summary/`, `/trends/`, `?date=` filter) executes `WHERE eaten_at::date = '...'` or `WHERE eaten_at BETWEEN ... AND ...`. Without this index, PostgreSQL performs a full sequential scan of the entire table for every request. With the index, it performs a range scan touching only the relevant date partition — O(log N + K) vs O(N).

### `meal_tags_gin_idx` — GIN on `tags` (jsonb)

```sql
CREATE INDEX meal_tags_gin_idx ON meals_meal USING GIN (tags);
```

**Justification:** The tag filter uses PostgreSQL's jsonb containment operator (`@>`): `WHERE tags @> '["vegetarian"]'`. B-tree indexes cannot accelerate containment queries on arrays. A GIN (Generalised Inverted Index) inverts the array elements, creating an entry for each distinct tag value that points to every row containing it. Tag filtering goes from O(N) full scan to O(K) where K is the number of matching rows.

---

## Logging Middleware

`RequestLoggingMiddleware` in `meals/middleware.py` wraps every WSGI call:

```python
def __call__(self, request):
    start = time.monotonic()
    response = self.get_response(request)
    duration_ms = round((time.monotonic() - start) * 1000)
    logger.info("%s %s → %s in %dms",
        request.method, request.get_full_path(),
        response.status_code, duration_ms)
    return response
```

**Sample log output:**
```
[2026-06-12 13:30:01 UTC] POST /api/meals/ → 201 in 28ms
[2026-06-12 13:30:02 UTC] GET /api/meals/summary/?date=2026-06-12 → 200 in 12ms
[2026-06-12 13:30:03 UTC] DELETE /api/meals/15/ → 204 in 8ms
```

Gunicorn's access log captures the same data at the transport level; the middleware adds it at the application level so it is available regardless of the reverse proxy.

---

## Frontend

### Architecture

```
App.jsx
 └── useMeals (hook)          ← all state lives here
      ├── AddMealForm          ← controlled form, client+server validation
      ├── SummaryBar           ← reads summary from hook, updates live
      ├── FilterBar            ← writes filter state to hook
      ├── MealList             ← reads meals + pagination from hook
      └── TrendsChart          ← reads trends from hook, emits bar clicks
```

### Component hierarchy

Every component receives **data and callbacks via props**. No component fetches data independently. This makes the data flow unidirectional and easy to trace.

### React state flow

`useMeals` is the single source of truth. When a meal is created:
1. `addMeal()` calls `createMeal()` (API).
2. On success, it **prepends the new meal to local state** — no full refetch.
3. It calls `fetchSummary()` to recompute the aggregated totals — one API call.
4. It calls `fetchTrends()` to update the chart.

When a meal is deleted:
1. `removeMeal()` calls `deleteMeal(id)` (API).
2. Filters `meals` array in state — the card disappears immediately.
3. Calls `fetchSummary()` — summary bar updates.
4. Calls `fetchTrends()`.

The page **never reloads**. The summary bar updates are visible immediately.

### Loading states

Every async operation has a `loading` flag. While `mealsLoading` is true, `MealList` renders skeleton cards. The submit button shows "Saving…" and is disabled during POST to prevent double-clicks.

### Error states

- API failure: a red banner with the error message and a retry hint.
- Empty filter result: a centred "No meals found" state with a hint to adjust filters.

### Filtering

`FilterBar` calls `updateFilters(patch)` from the hook. The hook merges the patch, resets `page` to 1, and `useEffect` triggers `fetchMeals`. All three filters (date, tag, search) combine in one API call.

### Trend interaction

Clicking a bar in `TrendsChart` calls `handleTrendBarClick(date)`. The hook sets `trendDateFilter` which overrides the date filter in both the meal list and summary bar. Clicking the same bar again or clicking "Clear" restores the original filters.

---

## Deployment

### Backend — Render

1. Create a new **Web Service** on Render pointing to the `backend/` folder.
2. Set **Build command:** `pip install -r requirements.txt`
3. Set **Start command:** `./entrypoint.sh`
4. Add all environment variables from `.env.example`.
5. Set `DATABASE_URL` to your Neon connection string.

**Live backend URL:** `https://plate-api-xxxx.onrender.com` *(replace after deploy)*

### Frontend — Vercel

1. Import the `frontend/` folder into Vercel.
2. Set **Build command:** `npm run build`
3. Set **Output directory:** `dist`
4. Set environment variable `VITE_API_BASE_URL` to your Render backend URL.

**Live frontend URL:** `https://plate-xxxx.vercel.app` *(replace after deploy)*

### CORS

`CORS_ALLOWED_ORIGINS` on the backend must list the Vercel URL exactly (no trailing slash, no wildcard). Example:

```
CORS_ALLOWED_ORIGINS=https://plate-xxxx.vercel.app
```

---

## AI Usage

- **Claude (Anthropic):** Used to generate the initial boilerplate structure for the serializer validation methods, the SVG chart scaffold, and the CSS variable token system. All generated code was reviewed line-by-line, corrected where it made incorrect assumptions (e.g. the GIN index syntax for JSONField, the `Coalesce` output_field requirement), and refactored to match the production architecture.
- **No AI was used for the core business logic** (gap-fill algorithm, duplicate detection, aggregation query structure) — these were written by hand.

---

## Tradeoffs

| Decision | Rationale |
|----------|-----------|
| Single Django app (`meals/`) | The domain is small; splitting into multiple apps would add indirection with no benefit. |
| `services.py` separate from `views.py` | Keeps views thin and makes business logic independently testable. |
| Python gap-fill instead of `generate_series` | A PostgreSQL `generate_series` CTE would also work with 1 query but requires raw SQL and loses ORM type-safety. The Python gap-fill is readable, equally fast for N ≤ 30, and stays within the 2-query budget. |
| No Redux | React's `useState` + a single custom hook is sufficient for this scope. Redux would add boilerplate with no benefit at this scale. |
| Hand-rolled SVG chart | Required by the spec; also demonstrates DOM-level understanding. |
| `color-mix()` for tag badge tints | Modern CSS; avoids hardcoding per-tag colours in JavaScript. |

---

## Scalability

| Concern | Current approach | At scale |
|---------|-----------------|----------|
| Read throughput | `CONN_MAX_AGE=60` (persistent connections) | Add PgBouncer, read replicas |
| Write throughput | Single Gunicorn process | Increase workers, horizontal scaling |
| Filtering | GIN + B-tree indexes | Partitioning by `eaten_at` date range |
| Summary | Single aggregate query | Redis cache with 30s TTL |
| Trends | 2 queries | Same — already optimal |

---

## Security

- All config via environment variables; no secrets in code.
- `DEBUG=False` in production.
- `CORS_ALLOWED_ORIGINS` whitelist — no wildcard `*`.
- Input validation at the serializer layer (never trust the client).
- `ALLOWED_HOSTS` enforced by Django.
- Nginx adds `X-Frame-Options`, `X-Content-Type-Options`, and `Referrer-Policy` headers.

---

## Future Improvements

- **Authentication:** JWT auth (djangorestframework-simplejwt) so multiple users can each have private meal logs.
- **Caching:** Redis cache on `/summary/` and `/trends/` with a 60-second TTL; invalidated on POST/DELETE.
- **Rate limiting:** `django-ratelimit` or a reverse-proxy rule to prevent API abuse.
- **Background jobs:** Celery + Redis for async tasks (e.g. daily nutrition report emails).
- **Testing:** pytest-django unit tests for every service function; Playwright E2E tests for the frontend.
- **CI/CD:** GitHub Actions pipeline (lint → test → build → deploy to Render/Vercel).
- **Nutritional database integration:** Auto-populate macros from a food database (Open Food Facts API) when creating a meal by name.

---

## What I Didn't Finish

No known missing functionality from the core specification.

The **AI Quick-Add bonus** (`POST /api/meals/quick-add/`) was not implemented. Implementing it correctly requires an LLM API key (Groq / OpenAI) and robust JSON parsing of free-form text. Given the 2-hour constraint, completing and hardening the core specification to production quality was the correct priority.
