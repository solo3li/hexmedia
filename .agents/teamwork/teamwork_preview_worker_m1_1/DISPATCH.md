# Dispatch: Worker M1 (Backend Auth, Multi-Tenancy & Data Isolation)

## Identity & Workspace
- Role: Implementation Worker
- Working directory: /root/hexmedia/.agents/teamwork/teamwork_preview_worker_m1_1
- Parent: f6e60383-d401-479c-9123-ee0a9cb852cc (teamwork_preview_orchestrator_1)

## Authoritative Inputs
- Read `/root/hexmedia/.agents/teamwork/ORIGINAL_REQUEST.md` completely.
- Read `/root/hexmedia/AGENTS.md` completely.
- Read `/root/hexmedia/PROJECT.md` completely.
- Read Survey 1 Analysis: `/root/hexmedia/.agents/teamwork/teamwork_preview_explorer_survey_1/analysis.md`
- Read Survey 1 Handoff: `/root/hexmedia/.agents/teamwork/teamwork_preview_explorer_survey_1/handoff.md`

## File Ownership
You exclusively own and may edit:
- `backend/ai_studio/auth.py` (new)
- `backend/ai_studio/models.py`
- `backend/ai_studio/api.py`
- `backend/ai_studio/migrations/`
- `backend/ai_studio/tests.py`

DO NOT edit frontend templates, `pytest.ini`, or other files.

## MANDATORY INTEGRITY WARNING
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Detailed Tasks
1. **Hybrid Auth Utilities (`backend/ai_studio/auth.py`)**:
   - HMAC-SHA256 JWT creation, decoding, expiration handling, secret key from Django settings.
   - `JWTAuth(HttpBearer)` class extracting Bearer token and returning `User` object or raising/returning None for 401.
   - Support both `JWTAuth` and standard Django session auth (`django_auth`) on Ninja API.
2. **Auth API Endpoints (`backend/ai_studio/api.py`)**:
   - `POST /api/auth/register`: Takes email, username (or auto-derived from email), password. Creates `User`, logs in via session, returns JWT access/refresh tokens and user info.
   - `POST /api/auth/login`: Authenticates username/email + password. Returns 401 on failure. On success, logs in via session, returns JWT access/refresh tokens.
   - `POST /api/auth/logout`: Clears session.
   - `GET /api/auth/me`: Requires auth, returns current user id, username, email.
3. **Multi-Tenancy Model & Migration**:
   - Add `user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='projects')` to `BookProject`.
   - Create migration and data migration backfilling existing 33 projects to admin user (id=1).
   - Ensure child models (`Scene`, `Character`, `Chapter`, `TimelineState`) isolate properly.
4. **API Authorization Gates**:
   - Configure Ninja API with `auth=[JWTAuth(), django_auth]`.
   - Ensure anonymous requests to generation/mutation endpoints receive HTTP 401.
   - Guard all project retrieval/mutation with `get_object_or_404(BookProject, id=project_id, user=request.auth)` so cross-tenant access returns 403 or 404.
5. **Verification**:
   - Add unit tests in `backend/ai_studio/tests.py` verifying registration, login, token refresh, anonymous rejection, and multi-tenant isolation.
   - Run verification commands: `./init.sh` and pytest.
   - Write handoff report with exact command outputs and evidence.


## 2026-10-24T03:37:18Z
[Message] timestamp=2026-10-24T03:37:18Z sender=f6e60383-d401-479c-9123-ee0a9cb852cc priority=MESSAGE_PRIORITY_HIGH content=You are Worker M1. Your working directory is /root/hexmedia/.agents/teamwork/teamwork_preview_worker_m1_1.
Read /root/hexmedia/.agents/teamwork/ORIGINAL_REQUEST.md, /root/hexmedia/AGENTS.md, /root/hexmedia/PROJECT.md, and /root/hexmedia/.agents/teamwork/teamwork_preview_worker_m1_1/DISPATCH.md.
Also read Survey 1 findings: /root/hexmedia/.agents/teamwork/teamwork_preview_explorer_survey_1/analysis.md and /root/hexmedia/.agents/teamwork/teamwork_preview_explorer_survey_1/handoff.md.

File Ownership:
You exclusively own and may edit:
- backend/ai_studio/auth.py (new)
- backend/ai_studio/models.py
- backend/ai_studio/api.py
- backend/ai_studio/migrations/
- backend/ai_studio/tests.py

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Detailed Tasks for Milestone 1:
1. Implement backend/ai_studio/auth.py:
   - HMAC-SHA256 JWT creation, decoding, expiration handling, secret key from settings.
   - JWTAuth(HttpBearer) class extracting Bearer token and returning User or raising/returning None for 401.
   - Integrate with standard Django session cookies (django_auth).
2. Implement Auth API Endpoints in backend/ai_studio/api.py:
   - POST /api/auth/register: Creates user, immediate auto-login via session, returns JWT access/refresh tokens and user details.
   - POST /api/auth/login: Authenticates credentials, returns 401 on bad password, returns JWT tokens and session cookie on success.
   - POST /api/auth/logout: Clears session.
   - GET /api/auth/me: Returns current user.
3. Multi-Tenancy Data Isolation:
   - Add user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='projects') to BookProject.
   - Create migration and data migration backfilling existing 33 projects to admin user (id=1).
   - Ensure child models (Scene, Character, Chapter, TimelineState) isolate properly.
4. Enforce Endpoint Authorization Gates:
   - Protect all project, generation, and mutation endpoints in api.py with auth=[JWTAuth(), django_auth].
   - Anonymous requests to generation/mutation endpoints MUST return HTTP 401 Unauthorized.
   - Filter all project queries with user=request.auth (e.g., get_object_or_404(BookProject, id=project_id, user=request.auth)). Cross-tenant access MUST return HTTP 403 or 404.
5. Verification:
   - Write unit tests in backend/ai_studio/tests.py for all auth and multi-tenancy isolation logic.
   - Run verification commands: ./init.sh and pytest. Confirm all tests pass and syntax compiles cleanly.
   - Write handoff report in /root/hexmedia/.agents/teamwork/teamwork_preview_worker_m1_1/handoff.md.
   - Send message to parent (f6e60383-d401-479c-9123-ee0a9cb852cc) when complete.


## 2026-10-24T03:50:12Z
[Message] timestamp=2026-10-24T03:50:12Z sender=f6e60383-d401-479c-9123-ee0a9cb852cc priority=MESSAGE_PRIORITY_HIGH content=**Context**: Milestone M1 Implementation
**Content**: Status check. What is your current step and what are you waiting for?
**Action**: Continue execution of steps 3, 4, 5, 6 and deliver handoff report.
