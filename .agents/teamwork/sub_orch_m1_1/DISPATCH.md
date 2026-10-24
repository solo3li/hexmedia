# Milestone 1 Sub-Orchestrator Dispatch: Auth & Data Isolation

## Identity & Workspace
- Role: Milestone 1 Sub-Orchestrator
- Working directory: /root/hexmedia/.agents/teamwork/sub_orch_m1_1
- Parent: f6e60383-d401-479c-9123-ee0a9cb852cc (teamwork_preview_orchestrator_1)

## Authoritative Inputs
- Read `/root/hexmedia/.agents/teamwork/ORIGINAL_REQUEST.md` completely.
- Read `/root/hexmedia/AGENTS.md` completely.
- Read `/root/hexmedia/PROJECT.md` completely.
- Survey reports: `/root/hexmedia/.agents/teamwork/teamwork_preview_explorer_survey_1/analysis.md` and `handoff.md`.

## Milestone Scope (M1)
1. Hybrid Authentication System:
   - Implement `backend/ai_studio/auth.py` with HMAC-SHA256 JWT encoding, decoding, token expiration, and `JWTAuth(HttpBearer)`.
   - Implement public endpoints:
     - `POST /api/auth/register` (creates user, auto-logs in, returns JWT access/refresh tokens and sets session cookie).
     - `POST /api/auth/login` (verifies credentials, returns JWT tokens and sets session cookie; returns HTTP 401 on bad password).
     - `POST /api/auth/logout` (clears session, revokes/invalidates token).
     - `GET /api/auth/me` (returns current user profile).
2. Multi-Tenancy Data Isolation:
   - Update `BookProject` model in `backend/ai_studio/models.py` to add `user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='projects')`.
   - Create and execute a safe Django migration that backfills the existing 33 orphan projects to `admin` (user id=1) so no data corruption occurs.
   - Enforce cascade isolation for child objects (`Scene`, `Character`, `Chapter`, `TimelineState`).
3. Endpoint Authorization Gates:
   - Configure `api = NinjaAPI(auth=[JWTAuth(), django_auth], ...)` in `backend/ai_studio/api.py`.
   - Protect all project, generation, and mutation endpoints. Anonymous access MUST return HTTP 401 Unauthorized.
   - Guard every project lookup with `get_object_or_404(BookProject, id=project_id, user=request.auth)`. User A accessing User B's project MUST return HTTP 403 or 404.
4. Verification:
   - Ensure unit tests in `backend/ai_studio/tests.py` verify registration, login, token refresh, anonymous rejection, and cross-tenant isolation.
   - Run verification via workers and ensure `./init.sh` passes cleanly.

Execute the Explorer -> Worker -> Reviewer -> Challenger -> Auditor cycle.
Report back via `send_message` with handoff when M1 gate passes.
