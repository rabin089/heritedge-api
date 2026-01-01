# HeritEdge Backend

FastAPI backend for heritage site contributions and management.

## Testing

See detailed instructions and results in `docs/TESTING.md`.

Quick start (Windows, inside venv):

```
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m pytest -q
```

## Project Structure

- `app/main.py` — FastAPI app entrypoint; includes `app/api/v1/routes.py`.
- `app/api/v1/` — API routers: `auth.py`, `contribution.py`, `heritage.py`, `admin.py`.
- `app/core/` — infrastructure: `database.py`, `security.py`.
- `app/schemas/` — Pydantic models (request/response DTOs).
- `app/crud/` — database access for entities.
- `alembic/` — database migrations.
- `tests/` — unit tests.

## Prerequisites

- Python 3.13
- PostgreSQL (local or remote)

## Environment Variables (.env)

Create a `.env` in project root. Defaults are shown where applicable.

```
# Database
DATABASE_URL=postgresql://postgres:admin@localhost:5432/heritedge_db

# Auth / JWT
SECRET_KEY=change_me
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_MINUTES=43200  # 30 days
```

Files reading these vars:
- `app/core/database.py` uses `DATABASE_URL`.
- `app/core/security.py` uses `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_MINUTES`.

## Setup

1) Create and activate virtualenv (or use existing):

```
python -m venv .venv
.venv\Scripts\activate
```

2) Install dependencies:

```
.venv\Scripts\python -m pip install -r requirements.txt
```

3) Database migrations (Alembic):

```
.venv\Scripts\alembic upgrade head
```

**Note**: The migration automatically creates initial admin users:
- **Superadmin**: `heritedgenepal@gmail.com` / `SuperAdmin123!`
- **Admin**: `admin@heritedgenepal.com` / `Admin123!`

⚠️ **Important**: Change these default passwords in production!

## Running the API

```
.venv\Scripts\python -m uvicorn app.main:app --reload
```

- Root: `GET /` — health message
- OpenAPI/Swagger: `GET /docs`
- OpenAPI JSON: `GET /openapi.json`

## Authentication & Roles

- OAuth2 password flow with bearer tokens.
- Endpoints in `app/api/v1/auth.py`:
  - `POST /login` — returns `access_token` and `refresh_token`.
  - `POST /refresh-token` — refreshes access token.
  - `GET /me` — current user profile.

Roles (`User.role`):
- `user` — can create/list/update/delete own contributions while pending; can resubmit rejected.
- `reviewer` — read-only access to admin lists.
- `admin` — approve/reject contributions; manage heritage sites (update/delete); view secured lists.
- `superadmin` — user/role management in `/admin/*` routes.

Role helpers in `app/api/v1/_role.py` (used by routers).

### Auth Policy

- Public (no token required):
  - `POST /login`, `POST /signup`, `POST /refresh-token`
  - `GET /heritage-sites`
  - `GET /heritage-sites/{id}`
  - `GET /heritage-sites/by-public/{uuid}`
- Protected (bearer token required):
  - All other endpoints, including contributions, favorites, notifications, and all `/admin/*` routes.

## Endpoints Overview

Auth (`app/api/v1/auth.py`):
- `POST /login` — form fields: `username`, `password`.
- `POST /refresh-token` — body: `{ "refresh_token": "..." }`.
- `GET /me` — bearer token required.

Contributions (`app/api/v1/contribution.py`):
- `POST /contributions` — user creates contribution.
- `GET /contributions/me` — list my contributions (optional `status` filter).
- `PUT /contributions/{id}` — update my pending contribution.
- `DELETE /contributions/{id}` — delete my pending contribution.
- `GET /contributions` — admin/reviewer list (optional `status`).
- `POST /contributions/{id}/approve` — admin approves; returns `heritage_site_id`.
- `POST /contributions/{id}/reject` — admin rejects; body `{ reason }`.
- `POST /contributions/{id}/resubmit` — user resubmits rejected (optional updated fields).

### Contributions examples (with images)

Create a contribution with primary and secondary images:

```bash
curl -X POST http://localhost:8000/contributions \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Ancient Temple",
    "region": "Asia",
    "category": "Cultural",
    "description": "A historic temple.",
    "tags": ["temple", "heritage"],
    "image_url": "https://cdn.example.com/images/temple-main.jpg",
    "secondary_images": [
      "https://cdn.example.com/images/temple-1.jpg",
      "https://cdn.example.com/images/temple-2.jpg"
    ]
  }'
```

Update a pending contribution (send only fields to change):

```bash
curl -X PUT http://localhost:8000/contributions/123 \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Updated description",
    "secondary_images": [
      "https://cdn.example.com/images/temple-1.jpg",
      "https://cdn.example.com/images/temple-3.jpg"
    ]
  }'
```

Resubmit a rejected contribution with updated image_url:

```bash
curl -X POST http://localhost:8000/contributions/123/resubmit \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "https://cdn.example.com/images/temple-main-v2.jpg"
  }'
```

Heritage Sites (`app/api/v1/heritage.py`):
- `GET /heritage-sites` — public approved sites with filters and search.
- `GET /heritage-sites/secured` — admin/reviewer list with filters and search.
- `GET /heritage-sites/{id}` — public by numeric id.
- `GET /heritage-sites/by-public/{uuid}` — public by UUID.
- `PUT /heritage-sites/{id}` — admin update.
- `DELETE /heritage-sites/{id}` — admin soft delete.

### Heritage listing query params

- `region` (str) — ILIKE match on region.
- `category` (str) — ILIKE match on category.
- `tag` (str) — exact match against any tag in the site tags array.
- `q` (str) — fuzzy ILIKE search across `name`, `region`, `description`, and tags string.
- `page` (int) — 1-based page index.
- `page_size` (int) — results per page (1-100).

### Heritage listing examples

Fuzzy search by name/region/description/tags:

```bash
curl "http://localhost:8000/heritage-sites?q=temple"
```

Filter by region/category/tag:

```bash
curl "http://localhost:8000/heritage-sites?region=asia&category=cultural&tag=temple"
```

Pagination with search:

```bash
curl "http://localhost:8000/heritage-sites?page=2&page_size=20&q=palace"
```

Favorites (`app/api/v1/favorites.py`):
- `POST /favorites/{site_id}` — add a site to current user's favorites.
- `DELETE /favorites/{site_id}` — remove a site from favorites.
- `GET /favorites` — list current user's favorite sites (`HeritageSiteOut[]`).

### Favorites examples

Add favorite:

```bash
curl -X POST http://localhost:8000/favorites/123 \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

Response:

```json
{"message": "Added to favorites"}
```

Remove favorite:

```bash
curl -X DELETE http://localhost:8000/favorites/123 \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

Response:

```json
{"message": "Removed from favorites"}
```

List favorites:

```bash
curl http://localhost:8000/favorites \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

Response (HeritageSiteOut[]):

```json
[
  {"id":1,"name":"Site A","region":"Asia","category":"Cultural","tags":["temple"]}
]
```

Notifications (`app/api/v1/notification.py`):
- `GET /notifications` — list current user's notifications.
- `POST /notifications/read` — mark notifications as read. Body: `{ "ids": [1,2,3] }`.
- `GET /notifications/unread-count` — get the count of unread notifications for the current user.
- `POST /notifications/read-all` — mark all notifications as read for the current user.

### Notifications examples

List my notifications:

```bash
curl http://localhost:8000/notifications \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

Response (NotificationOut[]):

```json
[
  {
    "id": 5,
    "recipient_email": "user@example.com",
    "type": "contribution_approved",
    "title": "Contribution #12 approved",
    "message": "Approved",
    "created_at": "2025-08-21T12:34:56+00:00",
    "read": false,
    "read_at": null
  }
]
```

Mark notifications as read:

```bash
curl -X POST http://localhost:8000/notifications/read \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"ids": [5,6]}'
```

Response:

```json
{"updated": 2}
```

Unread count:

```bash
curl http://localhost:8000/notifications/unread-count \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

Response:

```json
{"count": 5}
```

Mark all as read:

```bash
curl -X POST http://localhost:8000/notifications/read-all \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

Response:

```json
{"updated": 5}
```

Admin (`app/api/v1/admin.py`):
- `GET /admin/users` — superadmin list users.
- `POST /admin/users` — superadmin create user with role.
- `PUT /admin/users/{id}/role` — superadmin update role.
- `DELETE /admin/users/{id}` — superadmin delete user.
- `GET /admin/contributions/pending` — admin/reviewer list pending contributions with filters + pagination.
- `GET /admin/user/{user_id}/contributions` — admin/reviewer view a user's contribution history with pagination (optional status filter).

### Admin dashboard examples

List pending contributions with filters and pagination:

```bash
curl "http://localhost:8000/admin/contributions/pending?region=asia&category=cultural&q=temple&page=1&page_size=20" \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

Response:

```json
{
  "items": [ /* ContributionOut[] */ ],
  "total": 42,
  "page": 1,
  "page_size": 20
}
```

User contribution history (optional status):

```bash
curl "http://localhost:8000/admin/user/12/contributions?status=approved&page=1&page_size=10" \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

Response:

```json
{
  "user_id": 12,
  "user_email": "user@example.com",
  "items": [ /* ContributionOut[] */ ],
  "total": 5,
  "page": 1,
  "page_size": 10
}
```

## Data Lifecycle (Soft Delete)

- __Heritage Sites__: `DELETE /heritage-sites/{id}` marks a site as deleted (`is_deleted=true`). Deleted sites are excluded from public and secured listings.
- __Contributions__: deleting a pending contribution marks it as deleted. Deleted contributions are excluded from all lists. Records are retained for auditability.

Reminder: run migrations after pulling changes:

```
.venv\Scripts\alembic upgrade head
```

## Audit Logging

Both `heritage_sites` and `contributions` persist audit metadata:

- __approved_by/approved_at__: set when an admin approves a pending contribution; also stamped on the created heritage site.
- __updated_by/updated_at__: set when an authorized user updates a record (admin for heritage sites; owner/admin for contributions where applicable).
- __deleted_by/deleted_at__: set on soft delete operations.

These fields are stored in the database but are not exposed in public response schemas by default. If needed, add admin-only response schemas to surface them.

## Data Models (Schemas)

See `app/schemas/` for request/response shapes, e.g. `ContributionOut`, `HeritageSiteOut`, `UserOut`.

## Testing

- Detailed guide: `docs/TESTING.md`
- Run: `.venv\Scripts\python -m pytest -q`

## Troubleshooting

- Missing httpx when running tests: ensure `httpx` is installed (listed in `requirements.txt`).
- Alembic migration error: run `.venv\Scripts\alembic upgrade head`.
- JWT errors: verify `.env` has `SECRET_KEY`, `ALGORITHM`, and expiry minutes set.
- Database connection: verify `DATABASE_URL` and PostgreSQL is running.

## Notes

- Deprecation warnings recorded in tests: SQLAlchemy 2.0 `declarative_base`, Pydantic v2 `ConfigDict`, timezone-aware datetimes.

## Media Handling

This API stores only image URLs; clients manage uploads. The data model supports a primary image and multiple secondary images:

- `Contribution`: fields `image_url: str | None`, `secondary_images: List[str] | None` (`app/models/contribution.py`).
- `HeritageSite`: same fields for approved sites (`app/models/heritage_site.py`).
- Schemas include these fields (`app/schemas/contribution.py`).

### How to use today (simple URL flow)

1) Upload images from the frontend (or your own uploader service) to your storage (e.g., S3/GCS/Firebase Storage/CDN).
2) Get HTTPS URLs for the uploaded objects.
3) Submit contributions with:
   - `image_url`: primary image URL
   - `secondary_images`: array of image URLs

### Validation

- The API enforces HTTPS URLs and supports an optional domain allowlist.
- Configure allowed domains via `.env` (comma-separated):

```
IMAGE_ALLOWED_DOMAINS=img.mycdn.com,media.example.com
```

- If `IMAGE_ALLOWED_DOMAINS` is not set, only HTTPS is enforced.
- Validation logic lives in `app/api/v1/contribution.py` (`_validate_images`).

### Recommended production setup (optional)

- Direct client uploads to your bucket via presigned URLs (S3/GCS) or Firebase SDK.
- Keep bucket private; serve via CDN (CloudFront/Cloud CDN) if desired.
- Generate object keys like `uploads/{user_id}/{uuid}.{ext}`.
- Enforce size/MIME/type via storage policy (if using signed uploads) and your uploader.
- Optionally add image processing (thumbnails) and lifecycle rules for orphans.

This optional flow can be added later without breaking the current API (we would add `/uploads/sign`).
