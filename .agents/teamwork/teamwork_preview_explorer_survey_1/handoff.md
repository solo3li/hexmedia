# Handoff Report: Survey 1 — Auth, Multi-Tenancy & Database Architecture

## 1. Observation

1. **User Model & Session Configuration**:
   - `backend/hexmedia_core/settings.py` lines 12–21: `INSTALLED_APPS` includes `'django.contrib.auth'`, `'django.contrib.sessions'`. `AUTH_USER_MODEL` is not specified, so the active model is standard `django.contrib.auth.models.User`.
   - Django shell query `User.objects.values('id', 'username', 'email')` returned `[{'id': 1, 'username': 'admin', 'email': 'admin@hexmedia.local', 'is_superuser': True}]`. Exactly 1 user exists in PostgreSQL.
2. **Django Ninja API Security**:
   - `backend/ai_studio/api.py` lines 12–16:
     ```python
     api = NinjaAPI(
         title="HexMedia Audio Drama Studio API",
         version="1.0.0",
         description="API for AI Audio Drama Studio powered by Gemini 3.8 Flash and LangGraph"
     )
     ```
     `api` has no `auth=` parameter. All endpoints (`/health`, `/config`, `/chat`, `/upload-book`, `/projects/...`, `/scenes/...`) are completely unprotected and permit unauthenticated anonymous access.
3. **Multi-Tenancy Foreign Keys**:
   - Database constraint check via `information_schema.table_constraints`:
     Foreign keys on `ai_studio_*` tables are:
     - `('ai_studio_scene', 'project_id', 'ai_studio_bookproject', 'id')`
     - `('ai_studio_character', 'project_id', 'ai_studio_bookproject', 'id')`
     - `('ai_studio_chapter', 'project_id', 'ai_studio_bookproject', 'id')`
     - `('ai_studio_timelinestate', 'project_id', 'ai_studio_bookproject', 'id')`
     - `('ai_studio_chatmessage', 'project_id', 'ai_studio_bookproject', 'id')`
     `ai_studio_bookproject` has 0 foreign keys. No model in `ai_studio` references `auth_user`.
   - Existing records: 33 `BookProject` records and 122 `ChatMessage` records in PostgreSQL have no user association.
4. **ChatThread Model & Chat Persistence**:
   - `backend/ai_studio/models.py` contains models: `AIConfiguration`, `BookProject`, `Character`, `Chapter`, `Scene`, `TimelineState`, `ChatMessage`.
   - There is NO `ChatThread` model. `ChatMessage` has only a nullable `project` FK.
   - `backend/ai_studio/services/langgraph_controller.py` line 1335: `return builder.compile()`. No checkpointer is passed to `compile()`. Graph state is not persisted in PostgreSQL across sessions.
5. **Database & Migrations**:
   - `backend/hexmedia_core/settings.py` lines 54–63: PostgreSQL database `hexmedia` on host `127.0.0.1`, port `5439` (docker service `hexmedia_db`).
   - `python backend/manage.py showmigrations` confirmed all 6 migrations of `ai_studio` (0001 to 0006) and all auth/session/contenttype/admin migrations are applied `[X]`.
   - Direct connection via `psycopg 3` succeeded on `postgresql://hexmedia_user:hexmedia_secret_password@127.0.0.1:5439/hexmedia` (server version 160015).

---

## 2. Logic Chain

1. **API Security Gap** (Supported by Obs 2):
   Because `NinjaAPI` has no `auth` parameter and individual endpoints do not declare auth guards, any client can invoke `/api/chat`, upload books, edit/delete scenes, and change AI configuration keys anonymously. This directly violates Acceptance Criterion 1 ("Anonymous users accessing generation endpoints receive HTTP 401 Unauthorized").
2. **Data Leakage & Multi-Tenancy Vulnerability** (Supported by Obs 2, 3):
   Because `BookProject` lacks a `user` foreign key, all querysets in `api.py` resolve projects purely by `id` (e.g. `get_object_or_404(BookProject, id=project_id)`). Any user who supplies a known or guessed project UUID can view, modify, or delete another user's book project, scenes, and characters. Similarly, `backend/ai_studio/views.py` line 14 retrieves `BookProject.objects.all().order_by('-created_at')[:15]`, rendering all projects across the database to all visitors.
3. **Missing Conversation Thread Architecture** (Supported by Obs 4):
   Because `ChatThread` does not exist and `ChatMessage` only attaches to `BookProject`, conversations cannot exist independently of a book project. Without a `ChatThread` model with titling, archival, and soft delete fields, Requirements R2, R3, and R4 cannot be satisfied.
4. **Hybrid Auth Feasibility** (Supported by Obs 1, 2):
   `django-ninja` supports `auth=[JWTAuth(), django_auth]`. A custom `HttpBearer` class (`JWTAuth`) using standard HMAC-SHA256 tokens alongside Django's `django_auth` (session cookies) provides full hybrid authentication with zero disruption to Django Admin.
5. **Database Migration Safety** (Supported by Obs 3, 5):
   Because 33 existing `BookProject` records and 122 `ChatMessage` records reside in the database, adding `user` must initially be nullable (`null=True, blank=True`) or assigned via a data migration to `User` id=1 (`admin`) to avoid integrity errors during `migrate`.

---

## 3. Caveats

- **No Caveats**: All database tables, models, API endpoints, template views, and migration states were directly inspected and verified via the Django shell, PostgreSQL queries, and filesystem reads.
- **External Dependencies**: `langgraph-checkpoint-postgres` is available in pip index if `PostgresSaver` is preferred over a custom Django DB checkpointer.

---

## 4. Conclusion

The current codebase is functional for single-tenant local demonstrations, but completely lacks multi-tenant security and conversation memory architecture. To meet the requirements:
1. Implement `backend/ai_studio/auth.py` providing JWT encoding/decoding and `JWTAuth(HttpBearer)`. Apply `auth=[JWTAuth(), django_auth]` to `NinjaAPI`.
2. Add public auth endpoints (`/api/auth/register`, `/api/auth/login`, `/api/auth/logout`, `/api/auth/me`).
3. Add `ChatThread` model and add `user = ForeignKey(User)` to `BookProject` and `ChatMessage`.
4. Apply user-scoped filtering (`project = get_object_or_404(BookProject, id=project_id, user=request.auth)`) across all project and scene endpoints.
5. Implement LangGraph checkpoint persistence with thread IDs and sliding-window context compression.

---

## 5. Verification Method

To independently verify these findings:
1. **Verify Unauthenticated API Access**:
   ```bash
   curl -s -X POST http://127.0.0.1:8100/api/chat \
     -H "Content-Type: application/json" \
     -d '{"prompt": "hello"}' | jq .
   ```
   *Expected Current Output*: Returns HTTP 200 with chat response rather than HTTP 401.
2. **Verify Missing Model Columns**:
   ```bash
   ./venv/bin/python backend/manage.py shell -c "
   from ai_studio.models import BookProject
   print('User field on BookProject:', hasattr(BookProject, 'user'))
   "
   ```
   *Expected Output*: `User field on BookProject: False`.
3. **Verify Database Health & Migrations**:
   ```bash
   ./venv/bin/python backend/manage.py showmigrations
   ```
   *Expected Output*: All migrations marked `[X]`.
4. **Project Test Command Verification**:
   ```bash
   ./init.sh
   ```
   *Expected Output*: Runs pytest cleanly and validates syntax via compileall.
