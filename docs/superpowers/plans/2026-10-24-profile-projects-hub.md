# Profile & Projects Hub Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a comprehensive, interactive Profile & Projects Hub modal within HexMedia Studio enabling users to manage their audio/video projects, stream generated audio, preview video scenes, review scripts, and view account stats with full multi-tenant isolation.

**Architecture:** 
- Backend: Django Ninja endpoints in `backend/ai_studio/api.py` for project renaming (`PATCH /api/projects/{project_id}/rename`), project deletion (`DELETE /api/projects/{project_id}`), and enhanced media/statistics aggregation in `GET /api/profile/media`. All endpoints strictly enforce user ownership.
- Frontend: Single-page modern modal (`#profileModal`) in `backend/templates/chat/index.html` styled with Tailwind obsidian/lime theme, tabbed navigation (Projects, Audio, Video, Scripts, Stats), inline project renaming, project deletion with confirm dialog, and seamless project loading into the active chat. Accessible via header user menu and persistent sidebar navigation button.

**Tech Stack:** Django Ninja, Django ORM, PostgreSQL/SQLite, Vanilla JS (ES6+), Tailwind CSS (Dark Obsidian/Lime theme).

**Spec:** Brainstorming spec approved by user:
1. Interactive modern Modal/Overlay without page reload.
2. Tabs: Projects, Audio Clips, Video Scenes, Scripts, Account Stats.
3. Full Project Controls: open in chat, audio/video playback & download, rename, delete.
4. Dual Entry Points: user avatar menu in header + persistent sidebar button.
5. Strict Multi-User Isolation.

---

## Global Constraints

- Preserve all existing 147 tests without regression.
- Every API endpoint requires JWT and Session authentication with per-user data isolation.
- Do not add external frontend build steps or dependencies; use existing Tailwind CDN and inline JS pattern in `index.html`.
- Repository must remain restartable from `./init.sh`.

## Review Focus

1. User Isolation on Project Mutation: User A cannot rename or delete User B's project (must return 404 or 403).
2. Cascade cleanup: Deleting a project cleanly removes associated scenes, audio tracks, and chapters without orphan errors.
3. Unauthenticated access: Calling profile endpoints without valid JWT/session returns 401.
4. Dynamic loading into chat: Clicking "فتح في الشات" switches project in active state and loads its title and scenes.
5. Audio playback: Audio clips render with valid HTML5 audio tags and direct download links.

---

### Task 1: Backend API for Project Rename, Delete, and Media Stats

**Files:**
- Create: `backend/ai_studio/tests_profile.py`
- Modify: `backend/ai_studio/api.py:350-405`

**Steps:**
- [ ] **Step 1: Write failing tests in `backend/ai_studio/tests_profile.py`**
  - Test `GET /api/profile/media` returns aggregated stats (`projects_count`, `audio_tracks_count`, `video_scenes_count`, `total_duration_minutes`).
  - Test `PATCH /api/projects/{id}/rename` succeeds for project owner.
  - Test `PATCH /api/projects/{id}/rename` fails (404/403) for another user's project.
  - Test `DELETE /api/projects/{id}` successfully deletes owner's project.
  - Test `DELETE /api/projects/{id}` fails (404/403) for another user's project.
  - Test unauthenticated requests return 401.
- [ ] **Step 2: Run pytest to verify test failure**
  - Run: `./venv/bin/pytest backend/ai_studio/tests_profile.py`
  - Expected: Failures due to missing rename/delete endpoints and missing `stats` in `/api/profile/media`.
- [ ] **Step 3: Implement endpoints and schemas in `backend/ai_studio/api.py`**
  - Add schema `ProjectRenameRequest(title: str)`
  - Update `get_profile_media` to calculate and return `stats` dictionary.
  - Add `@api.patch("/projects/{project_id}/rename")` with user ownership verification.
  - Add `@api.delete("/projects/{project_id}")` with user ownership verification.
- [ ] **Step 4: Run pytest to verify all tests pass**
  - Run: `./venv/bin/pytest backend/ai_studio/tests_profile.py`
  - Expected: All tests in `tests_profile.py` pass.
- [ ] **Step 5: Commit changes**
  - Run: `git add backend/ai_studio/api.py backend/ai_studio/tests_profile.py && git commit -m "feat(api): add project rename, delete, and profile stats endpoints with multi-user isolation"`

---

### Task 2: Frontend Profile & Projects Modal & Dual Access Points

**Files:**
- Modify: `backend/templates/chat/index.html`
- Modify: `backend/ai_studio/tests_profile.py`

**Steps:**
- [ ] **Step 1: Add HTML markup for Profile & Projects Modal in `backend/templates/chat/index.html`**
  - Modal container `#profileModal` with dark backdrop blur.
  - Header: Avatar, username, email, stats badges, close button.
  - Navigation tab bar: Projects (مشاريعي), Audio (التسجيلات الصوتية), Video (المشاهد البصرية), Scripts (السيناريوهات), Stats (الإحصائيات).
  - Tab content panes `#profileTabProjects`, `#profileTabAudio`, `#profileTabVideo`, `#profileTabScripts`, `#profileTabStats`.
  - Empty states for each tab when no data exists.
- [ ] **Step 2: Add Dual Entry Points in `backend/templates/chat/index.html`**
  - In `userDropdownMenu`: Add "👤 الملف الشخصي والمشاريع" button calling `openProfileModal()`.
  - In Sidebar `#threadsSidebar`: Add persistent bottom button "الملف الشخصي والمشاريع" calling `openProfileModal()`.
- [ ] **Step 3: Add JavaScript logic in `backend/templates/chat/index.html`**
  - `openProfileModal(defaultTab)`: Opens modal, switches tab, and fetches data via `authFetch('/api/projects')` and `authFetch('/api/profile/media')`.
  - `closeProfileModal()`: Closes modal.
  - `switchProfileTab(tabName)`: Toggles active styles and displays corresponding tab container.
  - `renderProfileProjects(projects)`: Renders grid cards with genre badges, scenes count, duration, "فتح في الشات" button, rename button, and delete button.
  - `renderProfileAudio(audioTracks)`: Renders list of voice clips with inline `<audio>` player and MP3 download.
  - `renderProfileVideo(videoScenes)`: Renders visual cards with image thumbnail and download link.
  - `renderProfileScripts(scripts)`: Renders text script snippets with copy button.
  - `renderProfileStats(stats, user)`: Renders account summary cards with counters.
  - `openProjectInChat(projectId)`: Closes profile modal, switches `activeProjectId`, updates chat UI and fetches project scenes.
  - `renameProjectInProfile(projectId, currentTitle)`: Prompts user and issues `PATCH /api/projects/{projectId}/rename`, refreshes list.
  - `deleteProjectInProfile(projectId, projectTitle)`: Asks confirmation and issues `DELETE /api/projects/{projectId}`, refreshes list.
- [ ] **Step 4: Add UI verification test in `backend/ai_studio/tests_profile.py`**
  - Verify `index.html` contains `#profileModal`, `#profileTabProjects`, dual entry triggers, and required JS handler bindings.
- [ ] **Step 5: Run tests and verify**
  - Run: `./venv/bin/pytest backend/ai_studio/tests_profile.py`
  - Expected: All pass.
- [ ] **Step 6: Commit changes**
  - Run: `git add backend/templates/chat/index.html backend/ai_studio/tests_profile.py && git commit -m "feat(ui): implement profile and projects hub modal with tabbed media and dual access points"`

---

### Task 3: Full Verification & Documentation Update

**Files:**
- Modify: `feature_list.json`
- Modify: `progress.md`

**Steps:**
- [ ] **Step 1: Update `feature_list.json`**
  - Add feature entry `feat-009` "Profile & Projects Hub Modal".
- [ ] **Step 2: Update `progress.md`**
  - Record completion of Profile & Projects Hub with evidence and test counts.
- [ ] **Step 3: Run full harness verification**
  - Run: `./init.sh`
  - Expected: All tests pass (147 existing + new profile tests), python syntax checks clean.
- [ ] **Step 4: Commit final changes**
  - Run: `git add feature_list.json progress.md && git commit -m "docs: record feat-009 Profile & Projects Hub completion and verified state"`
