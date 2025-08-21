# Testing

This project includes unit tests covering RBAC permissions and soft-delete behavior.

## How to Run Tests

Windows (inside venv):

```
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m pytest -q
```

## Scope Covered

- RBAC in `tests/test_rbac.py`:
  - Reviewer can view contributions but cannot approve/reject
  - Admin can approve/reject contributions
  - Soft delete on heritage sites respected by secured listing
- Test fixtures in `tests/conftest.py` patch CRUD and auth to isolate endpoints.

## Current Result (sample)

```
.......                                                                                                      [100%]

================================================ warnings summary =================================================
app/core/database.py:14
  MovedIn20Warning: declarative_base() moved to sqlalchemy.orm.declarative_base() (SQLAlchemy 2.0)

pydantic/_internal/_config.py
  PydanticDeprecatedSince20: class-based Config is deprecated; use ConfigDict (does not affect functionality)

7 passed, 7 warnings in 0.06s
```

## Environment

- Python 3.13 (Windows)
- FastAPI, Starlette, SQLAlchemy 2.x, Pydantic 2.x, httpx

## Notes / Known Warnings

- SQLAlchemy: prefer `from sqlalchemy.orm import declarative_base` in `app/core/database.py`.
- Pydantic: consider replacing `class Config` with `model_config = ConfigDict(from_attributes=True)`.
- Datetime: use timezone-aware UTC (`datetime.now(datetime.UTC)`) in tests.

## Useful Files

- Tests: `tests/test_rbac.py`, `tests/conftest.py`
- Endpoints: `app/api/v1/*.py`
- Schemas: `app/schemas/*.py`
- Migrations: `alembic/versions/`
