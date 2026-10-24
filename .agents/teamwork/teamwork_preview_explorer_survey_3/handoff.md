# Handoff Report: UI Architecture, Media Management & Test Harness
**Agent**: Survey Explorer 3  
**Date**: 2026-10-24  
**Working Directory**: `/root/hexmedia/.agents/teamwork/teamwork_preview_explorer_survey_3`  
**Handoff Type**: Hard (Investigation complete)

---

## 1. Observation

1. **Frontend Studio Templates & Static Assets**:
   - `backend/templates/chat/index.html` (1,864 lines, 91,972 bytes) serves as the primary Chat Studio interface rendered by `chat_home_view(request)` in `backend/ai_studio/views.py:5-114`.
   - `backend/static/css/` and `backend/static/js/` are empty.
   - Styling uses Tailwind CDN (`<script src="https://cdn.tailwindcss.com"></script>` at line 14), Google Fonts (line 11), FontAwesome 6.5.1 CDN (line 40), and Marked.js CDN (line 43).
   - All client-side JavaScript is inline within `<script>` blocks (lines 441–1864).
   - DesignCombo Multi-track Web Studio exists as a separate Vite React app in `frontend/src/App.tsx` (664 lines, 28KB), running on port 5173, launched via `openDesignComboStudio()` (`backend/templates/chat/index.html:656-660`).

2. **Sidebar Structure & Current Gaps**:
   - The sidebar is rendered in `<aside id="sidebar" ...>` (`backend/templates/chat/index.html:110-162`).
   - Project list rendering (`backend/templates/chat/index.html:670-709`, `renderSidebarProjects()`):
     ```javascript
     list.innerHTML = projectsList.map(proj => {
       ...
       return `
         <button 
           onclick="selectProject('${proj.id}')" 
           class="w-full px-3 py-2.5 rounded-xl flex items-center justify-between text-right transition-all group ...
     ```
   - Observed omissions:
     - No search `<input>` element or search filter logic anywhere in `backend/templates/chat/index.html`.
     - No recency grouping logic (e.g. "Today", "Yesterday", "Previous 7 Days"). `projectsList` is rendered as an unpartitioned flat list.
     - No inline action icons for rename or delete.
     - No desktop collapsibility toggle: desktop class is static (`lg:relative lg:translate-x-0`).
     - Sidebar lists global `BookProject` records without user ownership or isolation.

3. **Visitor Prompt Onboarding & Auth Modals**:
   - `backend/templates/chat/index.html:1625-1634`:
     ```javascript
     async function handleSendMessage() {
       const input = document.getElementById('chatInput');
       const prompt = input.value.trim();
       if (!prompt && !selectedFile) return;
       document.getElementById('welcomeHero').classList.add('hidden');
       renderUserMessage(prompt || ...);
       input.value = '';
       ...
       const res = await fetch('/api/chat', ...);
     ```
   - Text is cleared immediately upon send without checking user auth state.
   - No login or registration modals exist. The only modal in `index.html` is `voiceModal` (`backend/templates/chat/index.html:405-435`).
   - Top header (`backend/templates/chat/index.html:168-231`) has no user avatar, profile menu, login button, or logout button.
   - `backend/ai_studio/api.py` initializes `api = NinjaAPI(...)` without `auth=...` (lines 12–16) and contains zero authentication endpoints or checks.

4. **User Profile Media Manager**:
   - Grep search for `profile` in `backend/` and `frontend/src/` returned 0 matches. No user profile view, page, modal, or endpoint exists.
   - Existing generated media assets:
     - Master audio drama WAV: produced by `@api.post("/projects/{project_id}/export")` (`backend/ai_studio/api.py:367-406`), uploaded to MinIO at `exports/{project.id}/master_audio_drama.wav`, tracked in `TimelineState.exported_audio_url` (`backend/ai_studio/models.py:240`).
     - Novel scripts: stored in `BookProject.raw_text`, `BookProject.summary`, `Chapter.summary`, `Scene.raw_text`, `Scene.vocalized_text` (`backend/ai_studio/models.py:70-71, 158-159, 191-192`).
     - Video scenes & visuals: `Scene.image_url`, `Scene.visual_prompt`, `Scene.motion_type`, and `TimelineState.exported_video_url` (`backend/ai_studio/models.py:207-221, 241`).
     - Film rendering endpoint: `@api.post("/projects/{project_id}/render-film")` (`backend/ai_studio/api.py:596-602`).

5. **Test Harness & Database Execution**:
   - `./init.sh` executes:
     ```bash
     $PYTHON_BIN -m pytest || [ $? -eq 5 ]
     $PYTHON_BIN -m compileall -q -x '(^|/)(\.?venv|env|node_modules|build|dist|__pycache__)(/|$)' .
     ```
   - Running `./init.sh` resulted in:
     `collected 0 items / no tests ran in 0.06s` (exit code 5 caught by `|| [ $? -eq 5 ]`).
   - `backend/ai_studio/tests.py` has 4 lines with 0 tests. Total test coverage is 0%.
   - `pytest` 9.1.1 is in `./venv`, but `pytest-django` is not installed; no `pytest.ini` or `conftest.py` exists.
   - Running `pytest` on Django files triggers `django.core.exceptions.ImproperlyConfigured`.
   - Docker container `hexmedia_db` runs PostgreSQL 16 on port 5439. `psql -c "\du"` confirmed `hexmedia_user` is a Superuser with `Create DB` privileges. `PYTHONPATH=backend DJANGO_SETTINGS_MODULE=hexmedia_core.settings` successfully connects to DB and returns `Projects count: 33`.

---

## 2. Logic Chain

1. **Frontend Architecture**:
   - Observation 1 establishes that HexMedia Studio is served via Django templates (`backend/templates/chat/index.html`) with inline JS and Tailwind CDN, while `frontend/src/` is a separate secondary tool for DesignCombo timeline editing on port 5173.
   - Therefore, the required Chat Studio UI enhancements (sidebar recency grouping, search, inline actions, auth modal, visitor onboarding, user profile menu, and media manager modal) must be integrated into `backend/templates/chat/index.html` and its backend controllers.

2. **Sidebar Deficiencies**:
   - Observation 2 demonstrates that the sidebar currently only lists `projectsList` as a flat collection without search, recency partitioning, rename/delete actions, desktop collapsibility, or user scoping.
   - Therefore, the sidebar must be refactored with a search input, a client-side date grouping function (`Today`, `Yesterday`, `Previous 7 Days`, `Older`), hover action buttons for inline renaming and soft-deletion, and an expandable/collapsible toggle for desktop.

3. **Visitor Onboarding Flow**:
   - Observation 3 shows that visitor prompts are cleared immediately (`input.value = ''`) and dispatched anonymously to `/api/chat`.
   - Therefore, a client-side buffer (`pendingPromptBuffer`) must hold the visitor's prompt, trigger the Login/Register modal, and automatically dispatch the buffered prompt only after token acquisition and session creation.

4. **Media Manager Gap**:
   - Observation 4 shows that while master audio tracks, scripts, and video scenes are stored in MinIO and PostgreSQL, no user profile or media library interface exists.
   - Therefore, a User Profile & Media Library component must be created with dedicated tabs for audio playback/download, script viewing/export, and video scene review, backed by a user-scoped `GET /api/profile/media` endpoint.

5. **Test Harness & DB Handling**:
   - Observation 5 shows that pytest currently collects 0 items, `pytest-django` is missing, and `./init.sh` swallows exit code 5.
   - Because `hexmedia_user` has `Create DB` privileges on PostgreSQL port 5439, adding `pytest-django` and a `pytest.ini` specifying `DJANGO_SETTINGS_MODULE = hexmedia_core.settings` and `pythonpath = backend` will allow pytest to cleanly run isolated database tests.

---

## 3. Caveats

- **Caveat 1**: LangGraph controller internals (`backend/ai_studio/services/langgraph_controller.py`) and continuous generation engine were only inspected for graph compilation and checkpointer presence; deep prompt engineering was left to Explorers 1 and 2.
- **Caveat 2**: MinIO storage relies on external endpoints configured in settings (`MINIO_ENDPOINT = http://127.0.0.1:9100`). In testing environments without running MinIO services, storage mocks or file-system fallbacks should be used.
- **Caveat 3**: No changes to source code files were made during this investigation (read-only constraint strictly enforced).

---

## 4. Conclusion

The current UI and test harness are functional as an early prototype but require four targeted additions to satisfy the requirements of `ORIGINAL_REQUEST.md`:
1. **Sidebar Enhancements**: Add search bar, recency grouping (`Today`, `Yesterday`, `7 Days`, `Older`), inline rename and delete actions with soft-delete backend support, and desktop collapsibility.
2. **Auth & Visitor Onboarding**: Implement sleek Login/Register modals in `backend/templates/chat/index.html`, add user profile menu to the top header, and intercept unauthenticated prompts into a pending buffer that auto-dispatches post-login.
3. **User Profile Media Manager**: Implement a Media Library modal with tabs for Audio Tracks (in-browser player & download), Scripts (synopsis & dialogue viewer), and Video Scenes (visual cards & video downloads), fed by a user-scoped `GET /api/profile/media` endpoint.
4. **Test Harness Fix**: Configure `pytest.ini` (`pythonpath = backend`, `DJANGO_SETTINGS_MODULE = hexmedia_core.settings`), install `pytest-django`, and build automated tests in `backend/ai_studio/tests.py` covering auth endpoints, multi-tenancy isolation gates, conversation persistence, and media manager endpoints.

---

## 5. Verification Method

To independently verify the observations:

1. **Verify Template & Static Assets**:
   ```bash
   ls -la /root/hexmedia/backend/static/css/ /root/hexmedia/backend/static/js/
   head -n 45 /root/hexmedia/backend/templates/chat/index.html
   ```
   *Expected*: CSS and JS directories are empty. Template loads Tailwind, FontAwesome, and Marked via CDN.

2. **Verify Lack of Auth & Sidebar Actions**:
   ```bash
   grep -inE "login|register|rename|delete_thread" /root/hexmedia/backend/templates/chat/index.html
   ```
   *Expected*: No matches found for login, register, rename, or thread deletion.

3. **Verify Test Harness & Pytest Exit Code 5**:
   ```bash
   /root/hexmedia/venv/bin/python -m pytest /root/hexmedia
   echo "Exit code: $?"
   ```
   *Expected*: `collected 0 items`, Exit code: 5.

4. **Verify Postgres Connectivity and DB Privileges**:
   ```bash
   PGPASSWORD=hexmedia_secret_password psql -h 127.0.0.1 -p 5439 -U hexmedia_user -d hexmedia -c "\du"
   ```
   *Expected*: `hexmedia_user` displays `Superuser, Create role, Create DB`.
