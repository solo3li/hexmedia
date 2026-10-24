# Survey Analysis: UI Architecture, Media Management & Test Harness
**Agent**: Survey Explorer 3  
**Date**: 2026-10-24  
**Working Directory**: `/root/hexmedia/.agents/teamwork/teamwork_preview_explorer_survey_3`  
**Reference Documents**: `/root/hexmedia/.agents/teamwork/ORIGINAL_REQUEST.md`, `/root/hexmedia/AGENTS.md`

---

## Executive Summary

The HexMedia platform is currently a single-tenant prototype with no user authentication, no multi-user data isolation, no separate `ChatThread` model, and no test suite (0% coverage). 

The frontend architecture consists of two distinct components:
1. **HexMedia Chat Studio**: A monolithic, RTL, dark-themed Django template at `backend/templates/chat/index.html` (1,864 lines, 92KB) served by `chat_home_view` on port 8100. All styling is inline or via Tailwind CDN, and all logic is contained in ~1,420 lines of inline JavaScript. The sidebar lacks search, recency grouping, inline actions (rename/delete), desktop collapsibility, and multi-user isolation.
2. **DesignCombo Multi-track Web Studio**: A Vite + React application in `frontend/src/App.tsx` (664 lines) running on port 5173 for multi-track audio/timeline manipulation, opened via URL parameter `?project_id=...`.

There are currently **no authentication modals**, **no visitor prompt onboarding flows**, **no user profile pages**, and **no media manager interfaces**. In addition, while PostgreSQL 16 is live with superuser permissions on port 5439, the automated test harness runs `pytest || [ $? -eq 5 ]` which collects 0 tests and ignores the exit code, leaving 0% test coverage.

---

## 1. Frontend Studio UI Architecture

### 1.1 Template & Static Asset Layout
- **Template Location**: `/root/hexmedia/backend/templates/chat/index.html`
- **View Controller**: `chat_home_view(request)` in `/root/hexmedia/backend/ai_studio/views.py` (lines 5–114).
  - Fetches `recent_projects_qs = BookProject.objects.all().order_by('-created_at')[:15]`.
  - Serializes `projects_list_json`, `initial_project_json`, `messages_json`, `available_voices_json` directly into the template context.
  - Does NOT filter by user (no authentication in place).
- **Static Assets Directory**:
  - `backend/static/css/` is completely empty.
  - `backend/static/js/` is completely empty.
  - External dependencies loaded via CDN in `<head>`:
    - Tailwind CSS CDN: `<script src="https://cdn.tailwindcss.com"></script>` with inline custom dark theme palette (`obsidian: #08080a`, `surface: #0e0e12`, `surfaceHover: #14141a`, `borderSubtle: #1c1c22`, `limeAccent: #e2ff44`, `muted: #71717a`, `light: #f4f4f6`).
    - Google Fonts: `IBM Plex Sans Arabic` and `JetBrains Mono`.
    - FontAwesome 6.5.1 CDN.
    - Marked.js CDN: `https://cdn.jsdelivr.net/npm/marked/marked.min.js`.
- **Inline JavaScript**:
  - Lines 441 to 1864 in `index.html` contain all client-side state, event handlers, API communication, and rendering logic.

### 1.2 Sidebar Structure & Capabilities
- **DOM Container**: `<aside id="sidebar" class="fixed lg:relative inset-y-0 right-0 w-72 lg:w-64 bg-surface border-l border-borderSubtle flex flex-col justify-between shrink-0 transition-transform duration-300 z-50 transform translate-x-full lg:translate-x-0 shadow-2xl lg:shadow-none">` (lines 110–162).
- **Current Header**:
  - Brand identity icon and "HexMedia" label (lines 114–123).
  - Mobile close button (`toggleSidebar(false)`, lines 125–130).
  - "New Chat / Project" button: `<button onclick="startNewChat()">` with shortcut label `Ctrl+K`. Triggers `window.location.href = '/'`.
- **Current Project / Thread List**:
  - Container: `<div id="projectsList" class="space-y-1 overflow-y-auto flex-1 pr-0.5">` (line 148).
  - Render function: `renderSidebarProjects()` (lines 670–709).
  - Iterates over `projectsList` array passed from Django context.
  - Renders a flat `<button onclick="selectProject('${proj.id}')">` with project title and status dot indicator (`bg-limeAccent`, `bg-amber-400 pulse-live`, etc.).
- **Current Sidebar Gaps & Missing Features**:
  1. **Search Filter**: No search input element, no keyboard search shortcuts, and no client-side filtering logic.
  2. **Recency Grouping**: No grouping by date/recency. Projects appear as an un-categorized flat list. Required grouping: "Today", "Yesterday", "Previous 7 Days", and "Older".
  3. **Inline Actions (Rename & Delete)**:
     - No rename button or inline contenteditable input.
     - No delete button or confirmation dialog.
     - No backend endpoints for renaming or deleting conversation threads/projects.
  4. **Desktop Collapsibility**:
     - On desktop (`lg:` breakpoint), the sidebar is static (`lg:relative lg:translate-x-0`).
     - There is no toggle button or chevron to collapse the sidebar into an icon-only strip or hide it entirely to maximize the chat canvas.
  5. **Thread Model Isolation**:
     - Lists global `BookProject` records instead of user-owned `ChatThread` objects.

---

## 2. Visitor Prompt Onboarding Flow & Authentication Modals

### 2.1 Current Visitor Flow & Vulnerabilities
- In `backend/templates/chat/index.html`:
  - Lines 381–396 contain the prompt input `#chatInput` and send button `#sendBtn`.
  - When a user types text and clicks Send or presses Enter:
    ```javascript
    async function handleSendMessage() {
      const input = document.getElementById('chatInput');
      const prompt = input.value.trim();
      if (!prompt && !selectedFile) return;
      document.getElementById('welcomeHero').classList.add('hidden');
      renderUserMessage(prompt || ...);
      input.value = ''; // Input is immediately cleared
      ...
      const res = await fetch('/api/chat', { ... });
    }
    ```
  - **Issues**:
    - Input buffer is immediately destroyed before checking if the user is authenticated.
    - No authentication token (`Authorization: Bearer <token>`) is sent.
    - The backend endpoint `/api/chat` processes the prompt unconditionally without user association.
- In `backend/templates/chat/index.html` headers:
  - Lines 168–231 define the top navigation bar.
  - There are NO login or register buttons, NO user profile icon, and NO user dropdown menu.
- In `backend/templates/chat/index.html` modals:
  - Lines 405–435 define `#voiceModal` (used strictly for character voice casting).
  - NO login modal and NO register modal exist in the template.

### 2.2 Target Implementation Requirements
1. **Auth Modal Dialogs (Login & Register)**:
   - Modern, sleek modal with dual tabs: "تسجيل الدخول" (Login) and "إنشاء حساب جديد" (Register).
   - Designed to seamlessly match `#08080a` obsidian and `#e2ff44` limeAccent styling.
   - Form fields: Email and Password (plus confirm password / name for registration).
   - Error feedback banners for invalid credentials or email collisions.
2. **Prompt Preservation & Automatic Dispatch**:
   - Check authentication status before dispatching `handleSendMessage()`.
   - If unauthenticated:
     - Do NOT clear `#chatInput.value`. Store in `pendingPromptBuffer = prompt`.
     - Open the Auth Modal.
     - Upon successful login or registration:
       - Store JWT token in `localStorage.setItem('hexmedia_token', token)`.
       - Update UI header with authenticated user profile chip.
       - Close modal.
       - Automatically dispatch `pendingPromptBuffer` to `/api/chat` with `Authorization: Bearer ${token}`.
       - Clear `pendingPromptBuffer` and clear `#chatInput.value`.
3. **Top Navigation User Menu**:
   - Authenticated: Display user avatar / email chip, dropdown containing "الملف الشخصي والمكتبة" (Profile & Media Library) and "تسجيل الخروج" (Logout).
   - Unauthenticated: Display "تسجيل الدخول" (Login) button opening the auth modal.

---

## 3. User Profile & Media Manager

### 3.1 Current System State
- There is NO profile page, template, modal, or endpoint in either `backend/` or `frontend/`.
- Grep queries for `profile` across `backend/` returned zero code matches.

### 3.2 Media Asset Generation & Storage Architecture
The backend already generates three major types of media assets, but lacks a centralized interface for users to browse, play, or download them:

| Media Type | Generation Mechanism | Current Storage / Location | Model Field Reference |
|---|---|---|---|
| **Audio Drama Master Tracks** | Concatenated 24kHz master WAV produced by `/api/projects/{id}/export` in `ai_studio/api.py` (lines 367–406). | MinIO S3 bucket `hexmedia-assets`: `exports/{project_id}/master_audio_drama.wav` | `TimelineState.exported_audio_url` |
| **Novel Scripts & Dramatizations** | Multi-chapter screenplay breakdown generated via Gemini 3.8 Flash (`ai_studio/services/gemini_service.py`). | PostgreSQL `BookProject`, `Chapter`, `Scene` tables. | `BookProject.summary`, `Chapter.summary`, `Scene.vocalized_text`, `Scene.raw_text`, `Scene.speaker_name` |
| **Video Scenes & Timeline Assets** | Scene visuals generated via Imagen / web archive (`ai_studio/services/visual_service.py`), Remotion film rendered via `/api/projects/{id}/render-film`. | MinIO S3 bucket `hexmedia-assets` and Remotion output bridge. | `Scene.image_url`, `Scene.visual_prompt`, `Scene.motion_type`, `TimelineState.exported_video_url` |

### 3.3 Target Media Manager Requirements
1. **User Profile & Media Library Modal / View**:
   - Accessible from the user navigation menu in HexMedia Studio.
   - Displays project statistics: total novels created, total duration of audio generated, total scenes rendered.
2. **Three-Tab Media Browser**:
   - **Audio Master Tracks Tab**:
     - Lists all completed projects with audio masters.
     - Embedded custom audio player (Play, Pause, Progress scrubber, Volume).
     - Direct "تحميل الصوت" (Download Audio WAV) button.
   - **Scripts & Synopses Tab**:
     - Displays novel title, synopsis, character voice casting list, and chapter dialogue breakdown.
     - "تحميل السيناريو" (Download Script) in TXT or JSON format.
   - **Video Scenes Tab**:
     - Visual grid of generated scene cards showing scene image thumbnails, motion badges (`zoom_in`, `pan_left`), speaker, dialogue snippet, and direct video preview/download.
3. **Soft-Deleted Projects Access**:
   - Archiving/deleting a thread from the active sidebar removes it from the sidebar, but keeps it accessible in this Media Library.
4. **Backend API Endpoint**:
   - `GET /api/profile/media`: Returns `{ audio_tracks: [...], scripts: [...], video_scenes: [...] }` strictly filtered by `request.auth` (authenticated user).

---

## 4. Existing Test Harness & Verification Suite

### 4.1 Harness Analysis (`./init.sh`)
- Script content (`/root/hexmedia/init.sh`):
  ```bash
  #!/bin/bash
  set -e
  echo "=== Harness Initialization ==="
  PYTHON_BIN="python3"
  if [ -f "./venv/bin/python" ]; then
    PYTHON_BIN="./venv/bin/python"
  fi
  echo "=== Running Tests ==="
  $PYTHON_BIN -m pytest || [ $? -eq 5 ]
  echo "=== Checking Syntax ==="
  $PYTHON_BIN -m compileall -q -x '(^|/)(\.?venv|env|node_modules|build|dist|__pycache__)(/|$)' .
  echo "=== Verification Complete ==="
  ```
- **Observations**:
  - Pytest returns exit code 5 when no tests are collected.
  - The script contains `|| [ $? -eq 5 ]`, which masks the complete absence of tests and reports `Verification Complete`.
  - `python3 -m compileall` verifies syntax across Python files, excluding virtual environments.

### 4.2 Test Coverage & Pytest Setup
- **Existing Tests**:
  - `backend/ai_studio/tests.py` has 4 lines:
    ```python
    from django.test import TestCase
    # Create your tests here.
    ```
  - Total test count: **0 tests**.
  - Total test coverage: **0%**.
- **Pytest Dependencies**:
  - `pytest` 9.1.1 is installed in `./venv`.
  - `pytest-django` is **NOT** installed.
  - No `pytest.ini`, `setup.cfg`, or `conftest.py` exist in the repository.
  - Running pytest directly on files importing Django models throws `django.core.exceptions.ImproperlyConfigured: Requested setting LOGGING_CONFIG, but settings are not configured.`

### 4.3 Database Handling in Tests
- **PostgreSQL Environment**:
  - Container `hexmedia_db` runs PostgreSQL 16 on host port `5439`.
  - User `hexmedia_user` password `hexmedia_secret_password` database `hexmedia`.
  - Verification via `psql -c "\du"` confirmed `hexmedia_user` has `Superuser, Create role, Create DB` privileges.
  - Therefore, the test runner can create and tear down test databases (e.g. `test_hexmedia`) without permission errors.
- **Recommendations for Enabling Automated Tests**:
  1. Add a `pytest.ini` in `/root/hexmedia/`:
     ```ini
     [pytest]
     DJANGO_SETTINGS_MODULE = hexmedia_core.settings
     pythonpath = backend
     testpaths = backend/ai_studio tests
     python_files = tests.py test_*.py *_tests.py
     ```
  2. Install `pytest-django` (`pip install pytest-django`) or provide a root `conftest.py` that configures `django.setup()`.
  3. Update `init.sh` to require tests to pass without swallowing exit code 5 once tests are created.

### 4.4 Required Test Matrix (Per Acceptance Criteria)
To satisfy the requirements in `ORIGINAL_REQUEST.md`, the test suite must implement:
1. **Auth & Multi-Tenancy Tests**:
   - `test_register_creates_user_and_tokens()`: Registers user, verifies JWT returned, verifies session cookie set.
   - `test_login_valid_credentials()`: Returns 200 with JWT and session.
   - `test_login_invalid_password_returns_401()`: Rejects with 401.
   - `test_anonymous_access_to_protected_api_rejected()`: Calls to `/api/chat`, `/api/upload-book`, `/api/projects/...` without token return 401.
   - `test_cross_user_data_isolation_gate()`: User A cannot read, modify, or delete projects/scenes/threads belonging to User B (HTTP 403 or 404).
2. **Conversation & Memory Tests**:
   - `test_first_message_triggers_ai_titling()`: Initial prompt produces concise title.
   - `test_thread_message_persistence()`: Messages persisted in database and reloaded in sequence.
   - `test_thread_switching_and_history_reloading()`: Switching threads returns correct conversation context.
   - `test_thread_soft_delete()`: Soft-deleting removes thread from active sidebar list while preserving project in media library.

---

## 5. Architectural Recommendations & Implementation Plan

### 5.1 Model Adjustments Needed
1. **User Association**:
   - Add `user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')` to `BookProject`.
   - Introduce dedicated `ChatThread` model (or extend `BookProject` with thread isolation fields):
     ```python
     class ChatThread(models.Model):
         id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
         user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_threads')
         project = models.OneToOneField(BookProject, on_delete=models.CASCADE, related_name='thread', null=True, blank=True)
         title = models.CharField(max_length=255, default="محادثة جديدة")
         is_archived = models.BooleanField(default=False)
         created_at = models.DateTimeField(auto_now_add=True)
         updated_at = models.DateTimeField(auto_now=True)
     ```
2. **Soft Delete**:
   - Add `is_archived = models.BooleanField(default=False)` or `is_deleted = models.BooleanField(default=False)`.

### 5.2 Frontend Studio UI Upgrades Needed
1. **Sidebar Modernization**:
   - Search input at top of project list with instant client-side filtering.
   - Date-based grouping function partitioning threads into:
     - "اليوم" (Today)
     - "أمس" (Yesterday)
     - "آخر 7 أيام" (Previous 7 Days)
     - "أقدم" (Older)
   - Inline action buttons on thread items (hover/focus):
     - Rename icon (pencil) triggering inline title editing.
     - Delete icon (trash) triggering confirmation and soft deletion.
   - Desktop sidebar toggle button in top header allowing collapse/expand of sidebar on large screens.
2. **Auth Modals & Visitor Onboarding**:
   - Clean modal component for Login & Register.
   - Prompt interception: on send, if unauthenticated, save prompt to buffer, open modal, and auto-dispatch upon auth success.
   - Top navigation profile dropdown with media library link and logout button.
3. **User Profile Media Manager**:
   - Modal or dedicated route with audio player, script viewer, and video scenes gallery.

### 5.3 Test Suite Integration
- Implement `pytest-django` configuration with `pytest.ini`.
- Implement comprehensive test cases in `backend/ai_studio/tests.py` covering auth, isolation, persistence, and media manager.
- Verify `./init.sh` runs cleanly and all tests pass.
