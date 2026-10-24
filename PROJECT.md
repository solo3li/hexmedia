# Project: HexMedia Studio Multi-User & Conversation Persistence

## Architecture
HexMedia Studio is a Django + Django Ninja application with a PostgreSQL database (port 5439) and MinIO object storage (port 9100). The generative pipeline utilizes LangGraph (`AudioDramaState`) and Gemini 3.8 Flash for continuous audio drama synthesis.

### Data Flow & Auth Architecture
- **Web Interface**: Django templates (`backend/templates/chat/index.html`) using Tailwind CDN, FontAwesome, and Marked.js.
- **Authentication**: Hybrid auth model.
  - Standard Django session cookies for Django admin and HTML views.
  - JWT Bearer tokens (stored in `localStorage`, transmitted via `Authorization: Bearer <token>`) for Django Ninja API.
- **Multi-Tenancy Isolation**:
  - `BookProject`, `ChatThread`, `ChatMessage`, and child media assets (`Scene`, `Character`, `Chapter`, `TimelineState`) are strictly owned by `User` (`auth.models.User`).
  - Queryset filters in Django Ninja endpoints enforce `user=request.auth`. Cross-user access returns HTTP 403 or 404. Anonymous access returns HTTP 401.
- **Conversation & Memory**:
  - `ChatThread` acts as the master container for chat sessions.
  - First turn triggers AI thread titling (3–5 word concise title).
  - Context window manager maintains bounded tokens using a sliding window (last 6 turns) + rolling smart summary of earlier turns.
  - Soft delete (`is_deleted=True`) archives threads from the active sidebar while retaining `BookProject` media for the user profile library.
- **LangGraph Checkpointing**:
  - State checkpointed via `PostgresSaver` (or DB checkpointer), keyed by `f"user_{user.id}:thread_{thread.id}"`.
  - Checkpointer pool connects to PostgreSQL port 5439 (`hexmedia_user`), with clean fallback to `MemorySaver` in isolated testing environments.

---

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Hybrid Auth (Session + JWT) | JWT generator, validator, `JWTAuth(HttpBearer)`, and session cookie support | M1 | ORIGINAL_REQUEST §R1 |
| 2 | Auth Endpoints | `POST /api/auth/register`, `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/me` | M1 | ORIGINAL_REQUEST §R1 |
| 3 | Model Ownership & Multi-Tenancy | `user` FK on `BookProject`, cascade isolation, migration with legacy backfill | M1 | ORIGINAL_REQUEST §R1 |
| 4 | API Endpoint Authorization Gates | Guard all Ninja endpoints with `auth=[JWTAuth(), django_auth]`; return 401 for anonymous | M1 | ORIGINAL_REQUEST §R1, AC |
| 5 | Strict Cross-Tenant Access Gates | Strict user-ownership checks (`get_object_or_404(..., user=user)`); return 403/404 | M1 | ORIGINAL_REQUEST §R1, AC |
| 6 | ChatThread Master Container Model | Dedicated `ChatThread` model (`id`, `user`, `title`, `project`, `summary`, `is_deleted`) | M2 | ORIGINAL_REQUEST §R2 |
| 7 | Thread CRUD Endpoints | `GET /api/threads`, `POST /api/threads`, `GET /api/threads/{id}`, `PATCH /api/threads/{id}`, `DELETE /api/threads/{id}` | M2 | ORIGINAL_REQUEST §R2 |
| 8 | AI Thread Titling | Automatic 3–5 word story concept title on first message in thread; inline rename | M2 | ORIGINAL_REQUEST §R2 |
| 9 | Soft Delete & Archival | Mark thread `is_deleted=True`; remove from sidebar; preserve BookProject media | M2 | ORIGINAL_REQUEST §R2 |
| 10 | Bounded Sliding Window + Rolling Summary | Sliding window (last 6 turns) + rolling smart summary to compress earlier context | M2 | ORIGINAL_REQUEST §R2 |
| 11 | LangGraph Postgres Checkpointing | State persistence keyed by unique thread_id per user/thread across sessions | M2 | ORIGINAL_REQUEST §R3 |
| 12 | Studio Sidebar with Recency Groups | Collapsible sidebar, grouped by Today, Yesterday, Previous 7 Days, Older | M3 | ORIGINAL_REQUEST §R4 |
| 13 | Sidebar Search & Inline Actions | Live search filter across threads; inline pencil (rename) and trash (delete) buttons | M3 | ORIGINAL_REQUEST §R4 |
| 14 | Auth Modals & Visitor Onboarding | Login/Register modals; buffer visitor prompt and auto-dispatch upon login | M3 | ORIGINAL_REQUEST §R1, §R4 |
| 15 | Header Profile Menu & Logout | User avatar/badge, user email display, logout trigger in header | M3 | ORIGINAL_REQUEST §R1, §R4 |
| 16 | User Profile Media Management UI | "My Projects & Media" modal/view with audio playback/download, scripts, and video scenes | M3 | ORIGINAL_REQUEST §R4 |
| 17 | Profile Media API | `GET /api/profile/media` returning user's audio tracks, scripts, and video scenes | M3 | ORIGINAL_REQUEST §R4 |
| 18 | E2E Opaque-Box Test Suite | Tiers 1-4 comprehensive test suite across auth, memory, persistence, and UI APIs | M4 | ORIGINAL_REQUEST AC |
| 19 | Passing Verification Gates | `./init.sh` runs cleanly, pytest passes 100%, and compileall passes | M4 | ORIGINAL_REQUEST AC |

---

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Backend Auth, Multi-Tenancy & Data Isolation | JWT auth utility, auth endpoints, User FK on BookProject, API auth guards, multi-tenancy access checks | none | IN_PROGRESS |
| M2 | Conversation Thread Architecture, Memory & LangGraph Persistence | ChatThread model, thread endpoints, AI titling, rolling summary, sliding window, LangGraph Postgres checkpointer | M1 | PLANNED |
| M3 | Studio UI: Sidebar, Modals, Onboarding & Profile Media Manager | Collapsible sidebar with recency groups & search, auth modals, visitor prompt buffer, profile media manager UI | M1, M2 | PLANNED |
| M4 | E2E Test Pass, Adversarial Hardening & Final Verification | Execute 100% of E2E test suite (Tiers 1-4), Tier 5 adversarial testing, verify ./init.sh | M1, M2, M3 | PLANNED |

---

## Interface Contracts

### 1. Auth Module (`backend/ai_studio/auth.py` ↔ `backend/ai_studio/api.py`)
- `generate_tokens_for_user(user: User) -> dict`: Returns `{"access_token": str, "refresh_token": str, "user": {"id": int, "username": str, "email": str}}`.
- `decode_jwt_token(token: str) -> Optional[User]`: Decodes Bearer JWT, validates signature and expiration, returns `User` or `None`.
- `class JWTAuth(HttpBearer)`: Extracts token from `Authorization: Bearer <token>`, returns authenticated `User` object or raises/returns `None` (triggering 401).
- `api = NinjaAPI(auth=[JWTAuth(), django_auth])`: Global or endpoint-level auth guard.

### 2. Thread & Memory Module (`backend/ai_studio/services/` ↔ `backend/ai_studio/api.py`)
- `generate_thread_title(prompt: str) -> str`: Calls Gemini 3.8 Flash (or fallback) to return a 3–5 word Arabic title.
- `update_rolling_summary(current_summary: str, past_messages: list) -> str`: Summarizes older turns beyond the sliding window.
- `get_thread_context(thread: ChatThread, window_size: int = 6) -> tuple[str, list]`: Returns `(summary, sliding_window_messages)`.
- `get_checkpointer(test_mode: bool = False) -> BaseCheckpointSaver`: Returns `PostgresSaver` in production, `MemorySaver` when under test.

### 3. Profile & Media Contract (`backend/ai_studio/api.py` ↔ Frontend UI)
- `GET /api/profile/media`: Requires auth.
  Response:
  ```json
  {
    "audio_tracks": [{"id": 1, "project_id": "...", "title": "...", "url": "...", "created_at": "..."}],
    "scripts": [{"id": 1, "project_id": "...", "title": "...", "raw_text": "...", "scenes_count": 5}],
    "video_scenes": [{"id": 1, "project_id": "...", "scene_number": 1, "image_url": "...", "video_url": "..."}]
  }
  ```

---

## Code Layout
- `backend/hexmedia_core/`: Django core configuration (`settings.py`, `urls.py`, `wsgi.py`).
- `backend/ai_studio/`:
  - `auth.py`: JWT utilities, `JWTAuth`, token expiration, security helpers.
  - `models.py`: Database models (`BookProject`, `ChatThread`, `ChatMessage`, `Scene`, `Character`, `TimelineState`).
  - `api.py`: Django Ninja API endpoints (auth, threads, chat, projects, scenes, profile media).
  - `views.py`: Django template view (`chat_home_view`).
  - `services/`:
    - `langgraph_controller.py`: `AudioDramaState`, nodes, compilation with checkpointer, runner.
    - `gemini_service.py`: Gemini client, thread titling, rolling summarizer.
    - `minio_client.py`: MinIO upload/download utilities.
  - `tests.py`: Unit and regression test suite.
- `backend/templates/chat/index.html`: Studio UI template (sidebar, auth modals, visitor onboarding, media manager modal).
- `pytest.ini`: Pytest configuration for Django test runner.
