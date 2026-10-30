# API Reference and Swagger Setup

## Base URLs

| Environment | URL |
|-------------|-----|
| Local | `http://localhost:8000` |
| API prefix | `http://localhost:8000/api` |
| Versioned extraction API | `http://localhost:8000/api/v1` |

## Job statuses

```text
pending -> in_progress -> completed
pending -> in_progress -> failed
pending -> in_progress -> cancelled
pending -> cancelled
```

| Status | Meaning |
|--------|---------|
| `pending` | Job created, not started |
| `in_progress` | Extraction running |
| `completed` | Extraction finished |
| `failed` | Extraction failed; read `error_message` |
| `cancelled` | Job cancelled by the client |

## Swagger setup

### Dependencies

`requirements.txt` contains:

```text
Django==5.2.18
djangorestframework==3.18.3
drf-yasg==1.21.18
```

Install with:

```bash
pip install -r requirements.txt
```

### Applications

`core/settings.py` registers DRF and drf-yasg:

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'drf_yasg',
    'api',
]
```

DRF settings used by the project:

```python
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
}
```

Swagger UI settings:

```python
SWAGGER_SETTINGS = {
    'USE_SESSION_AUTH': False,
    'DOC_EXPANSION': 'none',
    'DEFAULT_MODEL_RENDERING': 'example',
    'VALIDATOR_URL': None,
    'TAGS_SORTER': 'alpha',
    'OPERATIONS_SORTER': 'alpha',
}
```

### Schema view

`core/urls.py` builds the schema and serves it in several formats:

```python
from drf_yasg import openapi
from drf_yasg.renderers import SwaggerJSONRenderer, SwaggerYAMLRenderer
from drf_yasg.views import get_schema_view
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="Backend Project API",
        default_version='v1',
        description="API documentation for the Backend Project.",
        contact=openapi.Contact(email="contact@example.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)
```

Documentation routes:

| URL | Content |
|-----|---------|
| `http://localhost:8000/docs/` | Swagger UI |
| `http://localhost:8000/swagger/` | Swagger UI alias |
| `http://localhost:8000/redoc/` | ReDoc |
| `http://localhost:8000/swagger.json` | OpenAPI 2.0 schema as JSON |
| `http://localhost:8000/swagger.yaml` | OpenAPI 2.0 schema as YAML |
| `http://localhost:8000/` | Swagger UI |

The UI views use `cache_timeout=0`, so schema changes are visible without a
server restart.

### Annotations

Endpoints use `swagger_auto_schema` for tags, summaries, request bodies,
parameters, and response codes:

```python
@swagger_auto_schema(
    tags=['Extraction'],
    operation_summary='Start a new extraction job',
    request_body=ScanStartSerializer,
    responses={
        202: JobStatusSerializer,
        400: ErrorSerializer,
        401: ErrorSerializer,
        409: ErrorSerializer,
        502: ErrorSerializer,
    },
)
def post(self, request):
    ...
```

Tags used in the schema:

| Tag | Endpoints |
|-----|-----------|
| `Health` | `/api/v1/health`, `/api/health/`, `/api/health/ping/` |
| `Extraction` | `/api/v1/scan/*` |
| `Jobs` | `/api/v1/jobs/*` |
| `Users` | `/api/users/*` |

### Run locally

```bash
python manage.py migrate
python manage.py runserver
```

Open `http://localhost:8000/docs/`.

## Authentication

The Swagger UI and schema endpoints are public. The service itself does not
require a token, but the extraction start endpoint requires a HubSpot private
app access token.

Send the token in one of two places:

1. JSON field `api_token`
2. Header `X-API-Token`

Token rules:

- At least 20 characters
- Letters, numbers, `.`, `_`, and `-` only
- Stored as a SHA-256 fingerprint, never as plain text

With `HUBSPOT_VALIDATE_TOKEN_ON_START=True` (the default), the token is checked
against HubSpot before the job is created. A rejected token returns `401`. A
HubSpot connection or API error during validation returns `502`.

The project currently uses `AllowAny` on all endpoints. Add authentication and
permissions before exposing the API outside a development environment.

## Endpoints

### Health check

```http
GET /api/v1/health
```

Response `200 OK`:

```json
{
  "status": "ok",
  "message": "Data extraction service is running successfully"
}
```

### Start extraction

```http
POST /api/v1/scan/start
Content-Type: application/json
X-API-Token: pat-na1-...
```

Body:

```json
{
  "api_token": "pat-na1-your-private-app-token",
  "properties": ["dealname", "amount", "dealstage", "closedate"],
  "limit": 100,
  "archived": false
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `api_token` | string | Yes* | Required unless sent as `X-API-Token` |
| `properties` | array of strings | No | Defaults to the standard deal property list |
| `limit` | integer | No | 1 to 100; defaults to `HUBSPOT_PAGE_SIZE` |
| `archived` | boolean | No | Defaults to `false` |

Response `202 Accepted`:

```json
{
  "job_id": "4f5c1c1e-3b2a-4f0e-9f4b-6a7c8d9e0f12",
  "source": "hubspot",
  "status": "pending",
  "record_count": 0,
  "error_message": "",
  "created_at": "2026-10-30T10:00:00Z",
  "started_at": null,
  "completed_at": null,
  "cancelled_at": null
}
```

| Status | Reason |
|--------|--------|
| `202` | Job accepted |
| `400` | Missing or invalid token, invalid JSON, or invalid fields |
| `401` | HubSpot rejected the token |
| `409` | A job is already running for this token |
| `502` | Token validation could not reach HubSpot |

Example:

```bash
curl -X POST http://localhost:8000/api/v1/scan/start \
  -H "Content-Type: application/json" \
  -d '{"api_token": "pat-na1-your-private-app-token", "limit": 100}'
```

### Get status

```http
GET /api/v1/scan/status/{job_id}
```

Response `200 OK`:

```json
{
  "job_id": "4f5c1c1e-3b2a-4f0e-9f4b-6a7c8d9e0f12",
  "source": "hubspot",
  "status": "completed",
  "record_count": 5,
  "error_message": "",
  "created_at": "2026-10-30T10:00:00Z",
  "started_at": "2026-10-30T10:00:01Z",
  "completed_at": "2026-10-30T10:00:09Z",
  "cancelled_at": null
}
```

| Status | Reason |
|--------|--------|
| `200` | Job found |
| `404` | Job not found or ID is not a UUID |

### Get results

```http
GET /api/v1/scan/result/{job_id}?limit=100&offset=0
```

| Parameter | Type | Default | Notes |
|-----------|------|---------|-------|
| `limit` | integer | `100` | 1 to 500 |
| `offset` | integer | `0` | Records to skip |

Response `200 OK`:

```json
{
  "job_id": "4f5c1c1e-3b2a-4f0e-9f4b-6a7c8d9e0f12",
  "count": 5,
  "limit": 100,
  "offset": 0,
  "next_offset": null,
  "results": [
    {
      "source_id": "12345678901",
      "data": {
        "id_from_service": "12345678901",
        "dealname": "Acme renewal",
        "amount": "25000",
        "dealstage": "closedwon",
        "pipeline": "default",
        "closedate": "2026-11-15T00:00:00.000Z",
        "dealtype": "existingbusiness",
        "hubspot_owner_id": "98765",
        "createdate": "2026-10-01T09:12:00.000Z",
        "hs_lastmodifieddate": "2026-10-20T14:30:00.000Z"
      },
      "extracted_at": "2026-10-30T10:00:05Z"
    }
  ]
}
```

| Status | Reason |
|--------|--------|
| `200` | Job completed |
| `400` | Invalid `limit` or `offset` |
| `404` | Job not found |
| `409` | Job not completed |

Next page:

```bash
curl "http://localhost:8000/api/v1/scan/result/<job_id>?limit=100&offset=100"
```

Stop when `next_offset` is `null`.

### Cancel job

```http
POST /api/v1/scan/cancel/{job_id}
```

Response `200 OK`:

```json
{
  "job_id": "4f5c1c1e-3b2a-4f0e-9f4b-6a7c8d9e0f12",
  "status": "cancelled",
  "message": "Extraction job cancelled successfully."
}
```

| Status | Reason |
|--------|--------|
| `200` | Job cancelled |
| `404` | Job not found |
| `409` | Job already completed, failed, or cancelled |

### Remove job

```http
DELETE /api/v1/scan/remove/{job_id}
```

Response: `204 No Content`.

| Status | Reason |
|--------|--------|
| `204` | Job and records deleted |
| `404` | Job not found |

After removal, status and result calls return `404`.

### List jobs

```http
GET /api/v1/jobs/jobs?limit=100&offset=0&status=completed
```

| Parameter | Type | Default | Notes |
|-----------|------|---------|-------|
| `limit` | integer | `100` | 1 to 500 |
| `offset` | integer | `0` | Jobs to skip |
| `status` | string | none | `pending`, `in_progress`, `completed`, `failed`, or `cancelled` |

Response `200 OK`:

```json
{
  "count": 2,
  "limit": 100,
  "offset": 0,
  "next_offset": null,
  "results": [
    {
      "job_id": "4f5c1c1e-3b2a-4f0e-9f4b-6a7c8d9e0f12",
      "source": "hubspot",
      "status": "completed",
      "record_count": 5,
      "error_message": "",
      "created_at": "2026-10-30T10:00:00Z",
      "started_at": "2026-10-30T10:00:01Z",
      "completed_at": "2026-10-30T10:00:09Z",
      "cancelled_at": null
    }
  ]
}
```

| Status | Reason |
|--------|--------|
| `200` | Jobs returned |
| `400` | Invalid status or pagination values |

### Statistics

```http
GET /api/v1/jobs/statistics
```

Response `200 OK`:

```json
{
  "total_jobs": 10,
  "pending_jobs": 1,
  "in_progress_jobs": 1,
  "completed_jobs": 6,
  "failed_jobs": 1,
  "cancelled_jobs": 1,
  "total_records": 42,
  "average_extraction_time_seconds": 7.35
}
```

`average_extraction_time_seconds` is `null` when no completed job has timing
data.

### Example endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health/` | GET | Health check |
| `/api/health/ping/` | GET | Returns `{"message": "pong"}` |
| `/api/users/` | GET | List users |
| `/api/users/{id}/` | GET | Get one user |

## Response fields

### Job

| Field | Type | Description |
|-------|------|-------------|
| `job_id` | UUID string | Job identifier |
| `source` | string | Data source, currently `hubspot` |
| `status` | string | Job status |
| `record_count` | integer | Number of stored records |
| `error_message` | string | Failure details, empty on success |
| `created_at` | ISO 8601 | Creation time |
| `started_at` | ISO 8601 or null | Start time |
| `completed_at` | ISO 8601 or null | Finish time |
| `cancelled_at` | ISO 8601 or null | Cancellation time |

### Record

| Field | Type | Description |
|-------|------|-------------|
| `source_id` | string | HubSpot deal ID |
| `data` | object | Deal ID and extracted properties |
| `extracted_at` | ISO 8601 | Storage time |

Default deal properties:

```text
dealname, amount, dealstage, pipeline, closedate, dealtype, description,
hubspot_owner_id, createdate, hs_lastmodifieddate
```

### Errors

Error responses use this shape:

```json
{
  "error": "Job is not completed yet.",
  "status": "in_progress"
}
```

Serializer errors are keyed by field:

```json
{
  "api_token": [
    "Invalid API token provided. Provide a valid private app access token."
  ]
}
```

## Pagination

The result and job list endpoints use `limit` and `offset`:

- `limit` is the page size.
- `offset` is the number of records or jobs skipped.
- `next_offset` is the next page offset, or `null` on the last page.
- `count` is the total number of matching items.

```text
offset = 0
repeat:
    GET /api/v1/scan/result/{job_id}?limit=100&offset={offset}
    process results
    if next_offset is null: stop
    offset = next_offset
```

## HubSpot request behavior

The HubSpot service:

- Sends `Authorization: Bearer <token>` on every request.
- Retries `429` responses using the `Retry-After` header.
- Retries network failures with exponential backoff.
- Raises `RateLimitError` after `HUBSPOT_MAX_RETRIES` attempts.
- Raises `InvalidTokenError` on `401` and `403`.
- Sets the job to `failed` and stores the error if extraction cannot finish.

| Setting | Default | Description |
|---------|---------|-------------|
| `HUBSPOT_API_BASE_URL` | `https://api.hubapi.com` | API base URL |
| `HUBSPOT_API_TIMEOUT` | `30` | Request timeout in seconds |
| `HUBSPOT_PAGE_SIZE` | `100` | Default page size |
| `HUBSPOT_MAX_RETRIES` | `3` | Retry count |
| `HUBSPOT_VALIDATE_TOKEN_ON_START` | `True` | Check the token before creating a job |

## Tests

Run all tests:

```bash
python manage.py test
```

Run the live extraction test with a private app token:

```bash
HUBSPOT_TEST_TOKEN=pat-na1-your-token python manage.py test api.tests.RealExtractionTests
```

Check schema generation:

```bash
python manage.py shell -c "from django.conf import settings; settings.ALLOWED_HOSTS=['testserver']; from django.test import Client; c=Client(); print(c.get('/swagger.json').status_code)"
```

## Troubleshooting

| Problem | Check |
|---------|-------|
| `/docs/` returns `404` | `drf_yasg` is installed and `core.urls` is the root URLconf |
| Swagger UI has no endpoints | `path('api/', include('api.urls'))` exists |
| Schema request fails | Serializer fields and `swagger_auto_schema` types |
| Start returns `400` | Token format and JSON body |
| Start returns `401` | Token is valid and has `crm.objects.deals.read` |
| Start returns `409` | An active job exists for the same token |
| Job stays `pending` or `in_progress` | Service logs and background thread state |
| Job is `failed` | `error_message` in the status response |
| `DisallowedHost` | Add the host to `ALLOWED_HOSTS` |

## Production changes

1. Set `DEBUG=False`.
2. Set a new `SECRET_KEY`.
3. Set `ALLOWED_HOSTS` to the deployed domain.
4. Add authentication and throttling to the extraction endpoints.
5. Use PostgreSQL instead of SQLite.
6. Run `python manage.py collectstatic` and serve static files.
7. Run under Gunicorn or another WSGI server.
8. Move extraction to a task queue such as Celery or RQ instead of a background
   thread in the web process.
