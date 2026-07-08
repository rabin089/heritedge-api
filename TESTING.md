# HeritEdge Backend – Test Suite

This document explains the testing strategy, structure, and how to run the test
suite for the HeritEdge backend.

> **Status:** Test suite scaffolded and runnable. Covers RBAC, auth, heritage
> sites, contributions, favorites, and notifications. See *Roadmap* below for
> remaining items.

---

## 1. Quick start

```bash
# 1. Install test dependencies
pip install -r requirements.txt
pip install -r requirements-test.txt

# 2. Run all tests with a nice HTML report
pytest tests/ --html=test_report.html --self-contained-html -v

# 3. Open the report
#    test_report.html  →  double-click in your file browser
```

A console-only run is just:

```bash
pytest tests/ -v
```

---

## 2. Test strategy

| Layer | What we test | How |
|-------|--------------|-----|
| **Routing / HTTP** | URL paths, methods, status codes, response shape | FastAPI `TestClient` |
| **Auth / RBAC** | 401 on missing token, 403 on wrong role, 200 on right role | Dependency override with `DummyUser` |
| **CRUD** | Endpoints call the correct CRUD function, pass the right args | `monkeypatch` on CRUD modules |
| **Validation** | Bad inputs (non-HTTPS image, missing required field) | Send bad payloads, assert 4xx |
| **Database** | Smoke-tested via mock; full integration tests are TODO | Mock session in `conftest.py` |

### Design principles

1. **No real database required.** All tests use `MockDB` so the suite runs in
   under a second and on any machine.
2. **No external services.** MinIO, Firebase, and the real DB are stubbed.
3. **Tests are isolated.** Each test gets a fresh `TestClient` and
   `dependency_overrides` are cleared after the test.

---

## 3. File layout

```
tests/
├── conftest.py             # Shared fixtures (DummyUser, MockDB, role overrides)
├── test_rbac.py            # Role-based access control (reviewer / admin / user)
├── test_auth.py            # Signup, login, /me, refresh-token
├── test_heritage.py        # Public listing, secured list, CRUD by role
├── test_contribution.py    # Create, list, approve/reject workflow
├── test_favorites.py       # Add / remove / list favorites
└── test_notifications.py   # List, mark-read, unread-count
```

---

## 4. How the test fixtures work

### `DummyUser`
A lightweight stand-in for the real `User` model that bypasses SQLAlchemy
session binding. We `setattr` the fields we care about (email, role, id, etc.).

### `MockDB` / `MockQuery`
A no-op SQLAlchemy session. Returns `None` for `first()`, `[]` for `all()`,
and records `add()` / `commit()` calls so tests can assert on them.

### Role-based fixtures
`as_user`, `as_reviewer`, `as_admin`, `as_superadmin` automatically:
1. Override `get_current_user` to return a `DummyUser` with the right role.
2. Override `get_db` to yield a `MockDB`.
3. Clear overrides when the test ends.

### CRUD monkeypatching
Each `patch_*_crud` fixture replaces real CRUD functions with deterministic
stubs. This lets us control success/failure paths and avoid hitting the DB.

---

## 5. Coverage matrix

| Module | Endpoints | Tests |
|--------|-----------|-------|
| **Auth** | `/me` (GET/PUT), `/signup`, `/login`, `/refresh-token` | 11 |
| **Heritage Sites** | list, secured, get-by-id, update, delete | 9 |
| **Contributions** | create, list, update, delete, approve, reject, resubmit | 14 |
| **Favorites** | add, remove, list | 8 |
| **Notifications** | list, mark-read, unread-count, mark-all-read | 9 |
| **RBAC** | Cross-cutting role checks | 7 |
| **TOTAL** | | **~58 tests** |

---

## 6. Adding new tests

1. Place the file in `tests/` named `test_<feature>.py`.
2. Reuse the fixtures in `conftest.py` (`as_user`, `as_admin`, `patch_*_crud`).
3. Add a new CRUD patch fixture to `conftest.py` if your feature talks to a
   new CRUD module.
4. Run `pytest tests/ -v` to verify.

### Example
```python
def test_admin_can_delete_user(as_admin, patch_user_crud):
    resp = as_admin.delete("/users/123")
    assert resp.status_code == 200
```

---

## 7. Roadmap (not yet covered)

These endpoints are wired but not yet covered by automated tests:

- [ ] File upload (`/upload`) – needs MinIO mock
- [ ] Geocoding (`/geocoding`) – needs external API mock
- [ ] Festivals + Festival interactions
- [ ] Intangible heritage
- [ ] Site reviews
- [ ] User device tokens
- [ ] User settings
- [ ] Firebase login / account linking (full E2E)
- [ ] Full DB integration tests (Testcontainers + PostgreSQL)
- [ ] Load / performance tests (locust)

---

## 8. Troubleshooting

### "ModuleNotFoundError: No module named 'app'"
Run from the **project root** (where `app/` lives), not from `tests/`:
```bash
cd d:/Rabin Dulal/heritedge-backend
pytest tests/ -v
```

### "Address already in use" / live-reload issues
The test suite uses `TestClient`, which doesn't bind a port – you should
not see this. If you do, make sure no `uvicorn` process is running.

### A test fails with `AttributeError: ... 'NoneType' object has no attribute ...`
Check the fixture is included in the test signature, e.g.:
```python
def test_x(as_user, patch_contrib_crud):  # both fixtures!
    ...
```

---

## 9. CI integration

To run in GitHub Actions, add this step to your workflow:

```yaml
- name: Run tests
  run: |
    pip install -r requirements.txt
    pip install -r requirements-test.txt
    pytest tests/ --html=test_report.html --self-contained-html -v
- name: Upload test report
  if: always()
  uses: actions/upload-artifact@v4
  with:
    name: test-report
    path: test_report.html
```
