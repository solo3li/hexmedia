# Codebase Architecture Analysis: Multi-User Auth, Multi-Tenancy Isolation, and Database Configuration

**Date:** 2026-10-24  
**Author:** Survey Explorer 1  
**Working Directory:** `/root/hexmedia/.agents/teamwork/teamwork_preview_explorer_survey_1`  

---

## 1. Executive Summary

HexMedia Studio currently operates in a single-tenant, unauthenticated prototype state. While core features (LangGraph dramatization, Gemini 3.8 Flash, Gemini TTS, MinIO S3 storage, and Remotion bridge) are functional, the system has **no user authentication on API endpoints**, **no object-level ownership checks**, and **no tenant data isolation**.

Key findings:
1. **Zero API Security**: All 18 endpoints in `backend/ai_studio/api.py` are publicly accessible without authentication. Any anonymous client can create projects, execute chapters, delete scenes, trigger audio generation, or alter the global Gemini API key.
2. **Missing Multi-Tenancy Ownership**: None of the models in `backend/ai_studio/models.py` (`BookProject`, `Scene`, `Character`, `Chapter`, `TimelineState`, `ChatMessage`) have a `user` foreign key. There are 33 existing `BookProject` records and 122 `ChatMessage` records in PostgreSQL with no user assignment.
3. **No `ChatThread` Model**: Chat messages are currently tied directly to `BookProject` (or orphaned with `project=None`). There is no discrete thread abstraction to support ChatGPT-style conversation persistence, titling, soft deletion, or archival.
4. **No JWT Implementation**: Neither `pyjwt` nor JWT verification middleware is present, though `django-ninja 1.7.1` natively supports hybrid authentication via `auth=[JWTAuth(), django_auth]`.
5. **Database & Infrastructure Ready**: PostgreSQL 16.15 runs via Docker on port `5439` with database `hexmedia`. All 6 historical Django migrations are applied. Direct `psycopg 3` connections succeed.

---

## 2. Pillar 1: Multi-User Authentication & API Security

### 2.1 Current User Model & Session Configuration
- **Model**: Standard Django `django.contrib.auth.models.User` (via table `auth_user`). `AUTH_USER_MODEL` is not customized in `backend/hexmedia_core/settings.py`.
- **Fields in `auth_user`**: `id`, `password`, `last_login`, `is_superuser`, `username`, `first_name`, `last_name`, `email`, `is_staff`, `is_active`, `date_joined`.
- **Current Data**: Exactly 1 user exists in the database:
  - `id=1`, `username='admin'`, `email='admin@hexmedia.local'`, `is_superuser=True`.
- **Session Backend**: `django.contrib.sessions` with database storage (`django_session` table) is active and included in `MIDDLEWARE` (`SessionMiddleware`, `AuthenticationMiddleware`). Session cookies (`sessionid`) can be issued upon login/registration.

### 2.2 JWT Implementation Status
- **Installed Packages**: `django-ninja==1.7.1`, `Django==6.1.2`, `cryptography==50.0.2`. `pyjwt` is not installed currently, though `pip install pyjwt` is available without dependency conflicts. Alternatively, standard RFC-7519 HMAC-SHA256 (HS256) JWT generation and verification can be implemented with Python standard library (`hmac`, `hashlib`, `base64`, `json`) and `settings.SECRET_KEY`.
- **Hybrid Auth Strategy**:
  Django Ninja supports passing multiple security handlers to `NinjaAPI(auth=[...])`:
  ```python
  from ninja.security import HttpBearer, django_auth

  class JWTAuth(HttpBearer):
      def authenticate(self, request, token):
          payload = decode_jwt_token(token)
          if not payload or 'user_id' not in payload:
              return None
          try:
              return User.objects.get(id=payload['user_id'], is_active=True)
          except User.DoesNotExist:
              return None

  # Hybrid Auth: allows either Bearer JWT or Django Session Cookie
  api = NinjaAPI(
      title="HexMedia Studio API",
      auth=[JWTAuth(), django_auth]
  )
  ```
  - When a request supplies `Authorization: Bearer <token>`, `JWTAuth` runs.
  - When a request is from a browser session with a valid cookie, `django_auth` runs.
  - If authenticated, `request.auth` (or `request.user`) provides the authenticated `User` object.
  - If both fail, Django Ninja automatically returns `HTTP 401 Unauthorized`.
  - Public endpoints (e.g. `/api/auth/login`, `/api/auth/register`, `/api/health`) explicitly declare `auth=None`.

### 2.3 Existing API Endpoints Vulnerability Audit (`backend/ai_studio/api.py`)
All 18 endpoints are currently unauthenticated:

| Endpoint | Method | Current Auth | Impact / Vulnerability |
|---|---|---|---|
| `/health` | GET | None | Public health check (acceptable) |
| `/config` | GET | None | **High**: Exposes model configurations to anonymous users |
| `/config` | POST | None | **Critical**: Any user can overwrite global Gemini API key |
| `/chat` | POST | None | **Critical**: Anonymous prompts, unmetered AI token spend |
| `/upload-book` | POST | None | **Critical**: Unrestricted file uploads and processing |
| `/projects/{id}/update-characters` | POST | None | Cross-tenant project alteration |
| `/projects/{id}/approve-casting` | POST | None | Cross-tenant production triggering |
| `/projects/{id}/execute-chapter` | POST | None | Cross-tenant generation trigger |
| `/projects/{id}/chapters` | GET | None | Information disclosure across projects |
| `/projects/{id}/timeline` | GET | None | Information disclosure |
| `/projects/{id}/export` | POST | None | Uncontrolled master audio synthesis |
| `/projects/{id}/live-progress` | GET | None | Project state snooping |
| `/projects/{id}/start-continuous` | POST | None | Background worker spawn without auth |
| `/projects/{id}/pause-continuous` | POST | None | Denial of service on active generations |
| `/projects/{id}/resume-continuous` | POST | None | Unchecked background worker execution |
| `/projects/{id}/set-narration-mode` | POST | None | Project attribute tampering |
| `/scenes/{id}/regenerate` | POST | None | Unauthorized audio synthesis |
| `/scenes/{id}` | DELETE | None | **Critical**: Any client can delete arbitrary scene records |
| `/scenes/{id}/regenerate-visual` | POST | None | Unauthorized image generation / web crawler call |
| `/projects/{id}/render-film` | POST | None | Unchecked Remotion rendering execution |

### 2.4 Proposed Auth Endpoints
To satisfy Requirement R1:
1. `POST /api/auth/register` (`auth=None`):
   - Accepts `{ email, password, username? }`.
   - Validates uniqueness and password rules.
   - Creates `User`.
   - Calls `django.contrib.auth.login(request, user)` to set session cookie immediately.
   - Generates JWT access token (e.g., 7 days validity).
   - Returns `{ token, user: { id, email, username } }`.
2. `POST /api/auth/login` (`auth=None`):
   - Accepts `{ email, password }`.
   - Authenticates credentials (`authenticate(username=..., password=...)`).
   - If invalid: returns `HTTP 401 Unauthorized` with `{ "detail": "بيانات الدخول غير صحيحة" }`.
   - If valid: calls `login(request, user)` (session cookie) + generates JWT token.
   - Returns `{ token, user: { id, email, username } }`.
3. `POST /api/auth/logout`:
   - Calls `django.contrib.auth.logout(request)`.
   - Returns `{ success: true }`.
4. `GET /api/auth/me`:
   - Returns current user profile, project counts, and quotas.

---

## 3. Pillar 2: Multi-Tenancy Data Isolation & Object Ownership

### 3.1 Model Architecture & Foreign Key Mapping
Inspection of `backend/ai_studio/models.py` reveals the following entity graph:

```
User (auth_user)
  │
  ├── [MISSING] ──> BookProject (id, title, author, status, narration_mode, visual_style, ...)
  │                   │
  │                   ├── Character (project_id)
  │                   ├── Chapter (project_id)
  │                   ├── Scene (project_id, chapter_obj_id, speaker_id)
  │                   ├── TimelineState (project_id, 1:1)
  │                   └── ChatMessage (project_id, null=True)
  │
  └── [MISSING] ──> ChatThread (id, user_id, title, is_archived, is_deleted, summary, ...)
                      │
                      └── ChatMessage (thread_id)
```

#### Detailed Findings on Each Model:
1. **`BookProject`**:
   - Primary key: UUID.
   - Foreign keys: None.
   - **Vulnerability**: Completely unowned. Any authenticated or anonymous user can view or modify any project.
   - **Remediation**: Add `user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='projects', null=True, blank=True)`.
2. **`Character`, `Chapter`, `Scene`, `TimelineState`**:
   - Foreign keys: All have `project = models.ForeignKey(BookProject, on_delete=models.CASCADE)`.
   - Ownership cascade: Inherited from `BookProject.user`.
3. **`ChatMessage`**:
   - Currently: `project = models.ForeignKey(BookProject, on_delete=models.CASCADE, null=True, blank=True)`.
   - Has no `user` FK. If `project` is None, message belongs to nobody.
   - **Remediation**: Add `user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)` and `thread = models.ForeignKey('ChatThread', on_delete=models.CASCADE, null=True, blank=True, related_name='messages')`.
4. **`ChatThread` (New Model Required)**:
   - Needed for R2 and R3.
   - Structure:
     ```python
     class ChatThread(models.Model):
         id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
         user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_threads')
         project = models.ForeignKey(BookProject, on_delete=models.SET_NULL, null=True, blank=True, related_name='threads')
         title = models.CharField(max_length=255, default="محادثة جديدة")
         is_archived = models.BooleanField(default=False)
         is_deleted = models.BooleanField(default=False)  # Soft delete
         summary = models.TextField(blank=True, default="")  # Rolling smart summary
         created_at = models.DateTimeField(auto_now_add=True)
         updated_at = models.DateTimeField(auto_now=True)

         class Meta:
             ordering = ['-updated_at']
     ```

### 3.2 Queryset Filtering & Permission Gates
In `backend/ai_studio/api.py`:
- Current pattern:
  ```python
  project = get_object_or_404(BookProject, id=project_id)
  ```
- Secure multi-tenant pattern:
  ```python
  # Must filter by request.auth (or request.user)
  user = request.auth or request.user
  project = get_object_or_404(BookProject, id=project_id, user=user)
  ```
  If a user tries to access another user's project, `get_object_or_404` returns `HTTP 404 Not Found` (or explicit `HTTP 403 Forbidden`).
- For `Scene` operations:
  ```python
  scene = get_object_or_404(Scene, id=scene_id, project__user=user)
  ```

### 3.3 Information Leakage in Template Views (`backend/ai_studio/views.py`)
In `chat_home_view(request)`:
- Line 14:
  ```python
  recent_projects_qs = BookProject.objects.all().order_by('-created_at')[:15]
  ```
  This leaks the entire database's latest projects to any visitor loading the page!
- **Remediation**:
  ```python
  if request.user.is_authenticated:
      recent_projects_qs = BookProject.objects.filter(user=request.user).order_by('-created_at')[:15]
      # or active chat threads
      threads_qs = ChatThread.objects.filter(user=request.user, is_deleted=False).order_by('-updated_at')
  else:
      recent_projects_qs = BookProject.objects.none()
      threads_qs = []
  ```

### 3.4 Media & Asset Storage Isolation
- MinIO upload path convention:
  `audio/{project.id}/scene_{idx}.wav`
  `exports/{project.id}/master_audio_drama.wav`
- Because MinIO keys are partitioned by `project.id` (UUIDv4), securing the project metadata in Django ensures users cannot list or guess audio assets belonging to other users.
- In addition, the User Profile media library (`/api/user/media` or `/profile/`) will query `project.scenes.filter(status='GENERATED')` and `project.timeline.exported_audio_url` exclusively for `BookProject.objects.filter(user=request.user)`.

---

## 4. Pillar 3: Database Configuration & State Persistence

### 4.1 PostgreSQL Database Configuration
- **Host & Port**: Exposed on `127.0.0.1:5439` (mapped from Docker container `hexmedia_db` port 5432).
- **Credentials**:
  - User: `hexmedia_user`
  - Password: `hexmedia_secret_password`
  - Database: `hexmedia`
- **Settings in `backend/hexmedia_core/settings.py`**:
  ```python
  DATABASES = {
      'default': {
          'ENGINE': 'django.db.backends.postgresql',
          'NAME': os.getenv('POSTGRES_DB', 'hexmedia'),
          'USER': os.getenv('POSTGRES_USER', 'hexmedia_user'),
          'PASSWORD': os.getenv('POSTGRES_PASSWORD', 'hexmedia_secret_password'),
          'HOST': os.getenv('POSTGRES_HOST', '127.0.0.1'),
          'PORT': os.getenv('POSTGRES_PORT', '5439'),
      }
  }
  ```
- **Connection Health**: Verified via psycopg 3 (`server_version: 160015`). Connection is immediate and healthy.

### 4.2 Migrations Status & Migration Strategy
- `python backend/manage.py showmigrations` confirms:
  - `admin`: 0001–0003 [X]
  - `auth`: 0001–0012 [X]
  - `contenttypes`: 0001–0002 [X]
  - `sessions`: 0001 [X]
  - `ai_studio`: 0001–0006 [X]
- **Handling Existing Data**:
  - The database currently contains 33 `BookProject` records and 122 `ChatMessage` records.
  - Adding `user = models.ForeignKey(User, on_delete=models.CASCADE, ...)`:
    - To prevent migration failures on existing rows, the column should be declared with `null=True, blank=True`.
    - A data migration can automatically assign existing orphan projects/messages to the default `admin` user (`id=1`).
    - New creations via API will require `user=request.auth`.

### 4.3 LangGraph State Checkpoint Persistence
- **Current State in `backend/ai_studio/services/langgraph_controller.py`**:
  - Line 1335: `return builder.compile()`
  - There is **no checkpointer** passed to `compile()`. Graph state is purely in-memory and lost as soon as the node returns.
  - Calls to `audio_drama_agent.invoke(state_input)` do not provide `config={"configurable": {"thread_id": ...}}`.
- **Checkpointing Architecture**:
  - PostgreSQL is running and accessible on port `5439`.
  - Checkpointer package `langgraph-checkpoint-postgres` requires only `psycopg-pool` (all other dependencies are satisfied).
  - Alternatively, a database checkpointer model or `PostgresSaver.from_conn_string("postgresql://hexmedia_user:hexmedia_secret_password@127.0.0.1:5439/hexmedia")` can be initialized.
  - Compiling with `checkpointer`:
    ```python
    checkpointer = PostgresSaver(pool)
    checkpointer.setup()
    graph = builder.compile(checkpointer=checkpointer)
    ```
  - Invocations will supply `config={"configurable": {"thread_id": str(thread.id)}}`.
  - When a user resumes a thread, LangGraph retrieves the exact checkpoint, restoring intermediate state, character castings, and chapter generation status.

---

## 5. Architectural Recommendations & Implementation Plan

### Step 1: Authentication & JWT Utility (`backend/ai_studio/auth.py`)
- Implement `generate_jwt_token(user)` and `decode_jwt_token(token)`.
- Implement `JWTAuth(HttpBearer)`.
- Mount `[JWTAuth(), django_auth]` on `api = NinjaAPI(...)`.
- Add public endpoints: `POST /api/auth/register`, `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/me`.

### Step 2: Data Models & Multi-Tenancy Migrations (`backend/ai_studio/models.py`)
- Add `ChatThread` model (UUID, `user`, `project`, `title`, `is_archived`, `is_deleted`, `summary`).
- Add `user` FK to `BookProject` (`null=True`, linked to `User`).
- Add `user` and `thread` FKs to `ChatMessage`.
- Generate and run migration: `python backend/manage.py makemigrations ai_studio && python backend/manage.py migrate`.

### Step 3: Queryset Isolation & API Security Updates (`backend/ai_studio/api.py`)
- Update all project endpoints to resolve projects scoped by user:
  `project = get_object_or_404(BookProject, id=project_id, user=user)`
- Update scene endpoints to check ownership:
  `scene = get_object_or_404(Scene, id=scene_id, project__user=user)`
- Add thread endpoints:
  - `GET /api/threads` (grouped by Today, Yesterday, Previous 7 Days)
  - `PATCH /api/threads/{id}` (rename title)
  - `DELETE /api/threads/{id}` (soft delete: set `is_deleted=True`)
- Add user media library endpoint:
  - `GET /api/user/media` (returns all completed master audio dramas, scripts, video renders for current user).

### Step 4: AI Thread Titling & Rolling Context Memory
- In `gemini_service.py`, add `generate_thread_title(prompt: str) -> str` (3-5 word story concept in Arabic).
- On the first turn of a new thread, asynchronously or synchronously generate the title and save to `ChatThread.title`.
- Implement sliding window (last 6-8 messages) + rolling summary in `ChatThread.summary`.

### Step 5: Studio UI Updates (`backend/templates/chat/index.html`)
- Integrate Auth Modals (Login & Register dialogs with sleek obsidian/lime styling).
- Add top navigation User Profile menu (displaying user email/avatar, My Media link, and Logout button).
- Implement visitor prompt onboarding:
  - Capture prompt in memory / localStorage.
  - If unauthenticated, show Login/Register modal.
  - Upon success, store JWT in `localStorage`, set session cookie, reload threads, and auto-dispatch the pending prompt.
- Update sidebar to render user's threads grouped by recency (اليوم، أمس، آخر 7 أيام) with inline rename and delete buttons.

---

## 6. Verification Plan
1. **Automated Unit & Integration Tests**:
   - Write comprehensive tests in `backend/ai_studio/tests.py`:
     - Test user registration and immediate login.
     - Test JWT generation, validation, and invalid token rejection (401).
     - Test cross-user isolation: User A cannot access User B's project or scene (404/403).
     - Test anonymous access to `/api/chat` and `/api/upload-book` returns 401.
     - Test thread creation, automatic titling, soft deletion, and sliding window persistence.
2. **Harness Checks**:
   - Run `./init.sh` to ensure all tests pass and compileall passes cleanly.
