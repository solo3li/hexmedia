# Handoff Report: Challenger 2 — Milestone 1 Adversarial Verification

**Verdict**: **REQUEST_CHANGES**

---

## 1. Observation

Empirical testing was executed against Milestone 1 deliverables using a newly authored 26-test adversarial stress harness in `backend/ai_studio/test_challenger_m1_2.py`.

### A. Test Execution Summary
Command:
```bash
./venv/bin/pytest backend/ai_studio/test_challenger_m1_2.py -v
```
Results:
- **24 tests PASSED**
- **2 tests FAILED**

### B. Confirmed Passing Areas
1. **Refresh Token Security & Mechanics (9 tests passed)**:
   - `test_refresh_token_CANNOT_be_used_as_bearer_access_token_on_me`: Refresh token sent in `Authorization: Bearer <refresh_token>` to `/api/auth/me` is rejected with `HTTP 401 Unauthorized`.
   - `test_refresh_token_CANNOT_be_used_as_bearer_on_projects`: Rejected with `HTTP 401`.
   - `test_refresh_token_CANNOT_be_used_as_bearer_on_chat`: Rejected with `HTTP 401`.
   - `test_access_token_CANNOT_be_used_at_refresh_endpoint`: Sending access token to `/api/auth/refresh` is rejected with `HTTP 401` (`detail: "رمز التحديث غير صالح أو منتهي الصلاحية"`).
   - `test_expired_refresh_token_rejected_at_refresh_endpoint`: Rejected with `HTTP 401`.
   - `test_tampered_refresh_token_rejected`: Tampered signature/payload rejected with `HTTP 401`.
   - `test_jwt_alg_none_attack_rejected`: Token with `alg: "none"` rejected with `HTTP 401`.
   - `test_deactivated_user_cannot_refresh_or_access_endpoints`: User with `is_active=False` rejected with `HTTP 401` on both API access and token refresh.
   - `test_malformed_authorization_headers`: Malformed headers (`Bearer`, `Bearer `, `Token ...`, invalid base64) return `HTTP 401`.

2. **Hybrid Auth Behavior & Combinations (6 tests passed)**:
   - Case 1 (`neither`): Anonymous request without cookie or Bearer token returns `HTTP 401`.
   - Case 2 (`session only`): Session cookie without Bearer token returns `HTTP 200` and resolves to the session user.
   - Case 3 (`bearer only`): Bearer token without session cookie returns `HTTP 200` and resolves to the Bearer token user.
   - Case 4 (`both matching`): Both present for User A returns `HTTP 200` as User A.
   - Case 5 (`conflicting credentials`): Client has active session cookie for User A, but sends `Authorization: Bearer <User B token>`. In Django Ninja (`auth=[JWTAuth(), django_auth]`), `JWTAuth` runs first and resolves to User B. User B receives User B's profile (`/api/auth/me`), User B's projects (`/api/projects`), and cannot access User A's project (`/api/projects/{id}/chapters` returns `HTTP 404`). Zero cross-tenant data leakage occurs.
   - Case 6 (`valid session + invalid bearer`): When Bearer token is invalid/corrupt, `JWTAuth` returns `None`, and Django Ninja falls back to `django_auth`, returning `HTTP 200` as the session user.

3. **Database Constraints & Model Isolation (6 tests passed)**:
   - `test_unowned_project_hidden_from_projects_list`: Projects with `user=None` are not returned by `GET /api/projects`.
   - `test_unowned_project_endpoints_return_404`: Direct access to unowned projects (`/chapters`, `/timeline`, `/live-progress`, `/update-characters`, `/approve-casting`, `/execute-chapter`, `/export`) returns `HTTP 404 Not Found`.
   - `test_unowned_scene_endpoints_return_404`: DELETE and POST (`/regenerate`, `/regenerate-visual`) on scenes belonging to unowned projects return `HTTP 404`.
   - `test_chat_with_unowned_project_returns_404`: `/api/chat` with unowned `project_id` returns `HTTP 404`.
   - `test_user_chat_messages_are_strictly_isolated`: Chat history queries strictly filter by `user=request.auth`; no cross-tenant message leakage occurs.
   - `test_user_cascade_deletion_cleans_up_data`: Deleting a user cascades and removes their `BookProject` and `ChatMessage` records, leaving other users' records intact.

---

### C. Confirmed Vulnerabilities and Failures (2 Bugs)

#### Bug 1: Unhandled `ValueError` (HTTP 500) on Registration with Missing Email Local-Part
- **File**: `backend/ai_studio/api.py`, lines 122–139 (`register_endpoint`)
- **Observed Test Failure**: `DuplicateRegistrationStressTests::test_registration_with_empty_or_whitespace_fields`
- **Verbatim Error**:
  ```python
  File "/root/hexmedia/backend/ai_studio/api.py", line 139, in register_endpoint
      user = User.objects.create_user(username=username, email=email, password=data.password)
  File "/root/hexmedia/venv/lib/python3.12/site-packages/django/contrib/auth/models.py", line 150, in _create_user_object
      if not username:
          raise ValueError("The given username must be set")
  ValueError: The given username must be set
  ERROR django.request:log.py:283 Internal Server Error: /api/auth/register
  ```
- **Description**: In `register_endpoint`:
  ```python
  email = data.email.strip().lower()
  if not email or '@' not in email:
      raise HttpError(400, "يرجى إدخال بريد إلكتروني صالح")
  ...
  base_username = (data.username.strip() if data.username else email.split('@')[0])
  ```
  When a client registers with `email="@nodomain"` (or any email without characters before `@`), `'@' in email` is `True`. However, `email.split('@')[0]` evaluates to `""`.
  This passes `""` to `User.objects.create_user(username="", ...)`. Django's auth model raises `ValueError("The given username must be set")`, which is uncaught and crashes the API with `HTTP 500 Internal Server Error` instead of returning `HTTP 400 Bad Request`.

#### Bug 2: Unhandled `IntegrityError` (HTTP 500) on Concurrent Duplicate User Registration
- **File**: `backend/ai_studio/api.py`, lines 128–140 (`register_endpoint`)
- **Observed Test Failure**: `ConcurrentRegistrationStressTests::test_concurrent_registrations_same_email`
- **Verbatim Error**:
  ```python
  File "/root/hexmedia/backend/ai_studio/api.py", line 139, in register_endpoint
      user = User.objects.create_user(username=username, email=email, password=data.password)
  File "/root/hexmedia/venv/lib/python3.12/site-packages/psycopg/cursor.py", line 117, in execute
      raise ex.with_traceback(None)
  psycopg.errors.UniqueViolation: duplicate key value violates unique constraint "auth_user_username_key"
  DETAIL:  Key (username)=(concurrent_race_da3dc74d) already exists.
  django.db.utils.IntegrityError: duplicate key value violates unique constraint "auth_user_username_key"
  ERROR django.request:log.py:283 Internal Server Error: /api/auth/register
  ```
- **Description**: `register_endpoint` checks existence via `User.objects.filter(email__iexact=email).exists()` and `User.objects.filter(username__iexact=username).exists()` prior to insertion.
  Under concurrent registration requests for the same email or username (or when derived usernames collide in flight), two threads simultaneously pass the existence check.
  The second thread to execute `User.objects.create_user()` hits PostgreSQL's unique constraint `auth_user_username_key`, throwing `django.db.utils.IntegrityError`.
  Because `register_endpoint` has no `try ... except IntegrityError:` handler, the exception uncaught in Django Ninja crashes the request with `HTTP 500 Internal Server Error` rather than returning `HTTP 400 Bad Request` or retrying username generation.

---

## 2. Logic Chain

1. **Input Validation Logic**:
   - `register_endpoint` relies on `'@' in email` to validate email addresses and derive `base_username = email.split('@')[0]`.
   - For emails like `@domain` or `@example.com`, `'@' in email` is true, but `base_username` is empty (`""`).
   - Django's `UserManager.create_user` explicitly requires a non-empty `username`. Passing an empty string raises `ValueError`.
   - Because `register_endpoint` does not validate that `base_username` is non-empty, nor does it catch `ValueError`, requests crash with HTTP 500.
2. **Concurrency Race Condition Logic**:
   - Web applications receive asynchronous concurrent requests. When two users or duplicate form submissions trigger registration at the same millisecond, the application-level `.exists()` check is non-atomic.
   - The database constraint `auth_user_username_key` is the ultimate consistency gate.
   - When a collision occurs, PostgreSQL enforces integrity and raises `UniqueViolation` / `IntegrityError`.
   - Without an exception handler catching `IntegrityError`, the API server returns an unhandled HTTP 500 crash instead of a user-facing HTTP 400/409 validation response.

---

## 3. Caveats

- Refresh token revocation: Currently JWTs are stateless HMAC tokens without a database-backed revocation blocklist (logging out invalidates the Django session, but access JWTs remain valid until their 7-day expiration). This satisfies Milestone 1 requirements, but is noted for future consideration.
- Foreign key nullability: `BookProject.user` and `ChatMessage.user` retain `null=True, blank=True` in the Django model to support the legacy migration backfill. While unowned records cannot be accessed via the API (all endpoints enforce `user=request.auth` returning 404), tightening `null=False` at the DB level could be evaluated after all legacy data migrations are completed.

---

## 4. Conclusion

**Verdict**: **REQUEST_CHANGES**

Milestone 1 auth implementation is largely solid:
- 100% of token security tests passed (refresh tokens cannot be used as access tokens, alg:none attacks fail, deactivated accounts blocked).
- 100% of hybrid auth combination tests passed (proper precedence, no cross-tenant leakage between session cookie and Bearer token).
- 100% of database isolation gates passed (unowned projects return 404, chat messages isolated, cascade delete verified).

However, **Worker M1 must address the two registration edge case crashes**:
1. **Fix empty username / email prefix validation**: In `backend/ai_studio/api.py` (`register_endpoint`), validate that `base_username` is non-empty and email has valid format before `@`. Reject with `HttpError(400, "يرجى إدخال بريد إلكتروني صالح")`.
2. **Catch `IntegrityError` during user creation**: Wrap `User.objects.create_user()` in `try ... except IntegrityError:` in `register_endpoint` to catch race condition collisions and return `HttpError(400, "البريد الإلكتروني أو اسم المستخدم مسجل بالفعل")` (or regenerate username suffix).

---

## 5. Verification Method

To reproduce and verify fixes:

1. **Run the Duplicate Registration Test**:
   ```bash
   DJANGO_SETTINGS_MODULE=hexmedia_core.settings PYTHONPATH=backend ./venv/bin/pytest backend/ai_studio/test_challenger_m1_2.py -k "DuplicateRegistrationStressTests" -v
   ```
   *Expected Output after fix*: 4 passed in ~9s.

2. **Run the Concurrent Registration Test**:
   ```bash
   DJANGO_SETTINGS_MODULE=hexmedia_core.settings PYTHONPATH=backend ./venv/bin/pytest backend/ai_studio/test_challenger_m1_2.py -k "ConcurrentRegistrationStressTests" -v
   ```
   *Expected Output after fix*: 1 passed in ~5s.

3. **Run the Full Challenger 2 Stress Suite**:
   ```bash
   DJANGO_SETTINGS_MODULE=hexmedia_core.settings PYTHONPATH=backend ./venv/bin/pytest backend/ai_studio/test_challenger_m1_2.py -v
   ```
   *Expected Output after fix*: 26 passed in ~40s.

4. **Run Standard Harness Verification**:
   ```bash
   ./init.sh
   ```
