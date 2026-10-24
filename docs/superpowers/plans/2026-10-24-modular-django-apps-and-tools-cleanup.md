# Modular Django Apps Architecture & Tools Menu Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor HexMedia from a coupled single-app monolith into a clean 4-app modular Django architecture (`core`, `book_drama`, `story_writer`, `image_video`), remove the redundant voice trigger tool from the UI, and rename the visual studio tool to "إنتاج فيلم وفيديو بالصور", while maintaining 100% test pass rate across all 154 tests and zero database disruption.

**Architecture:**
- Frontend: Refine `backend/templates/chat/index.html` by removing tool #3 ("تنفيذ وتوليد الصوت الآن") and renaming tool #4 to "إنتاج فيلم وفيديو بالصور" with updated labels and pills.
- Backend Modular Apps:
  1. `backend/core`: Auth (JWT), User management, `ChatThread`, `ChatMessage`, `AIConfiguration`, memory services, health checks.
  2. `backend/book_drama`: `BookProject`, `Chapter`, `Character`, book ingestion/parser (`book_parser.py`), casting, and novel breakdown.
  3. `backend/story_writer`: Turn-by-turn drama director, screenplay generation, narration mode management.
  4. `backend/image_video`: `Scene`, `TimelineState`, continuous generation engine, visual frame generation (`image_search.py`), and Remotion bridge.
- Preservation & Shims:
  - Models define explicit `db_table` matching existing schema (`ai_studio_bookproject`, `ai_studio_scene`, etc.) for zero data loss.
  - `backend/ai_studio/models.py` serves as a clean facade re-exporting modular models for total backward compatibility.
  - `INSTALLED_APPS` registers the new modular apps.

**Tech Stack:** Django, Django Ninja, PostgreSQL/SQLite, Tailwind CSS, Vanilla JS.

---

## Global Constraints

- All 154 existing tests must pass via `./init.sh`.
- Do not drop or rename existing database tables (`db_table` preservation).
- Python compileall check must pass with zero syntax errors.
- Monolithic chat template in `backend/templates/chat/index.html` must remain fully responsive and functional.

---

### Task 1: Clean Up Tools Popup Menu in Frontend UI

**Files:**
- Modify: `backend/templates/chat/index.html:332-400`
- Modify: `backend/templates/chat/index.html:985-1025`
- Test: `backend/ai_studio/tests_profile.py`

**Steps:**
- [ ] **Step 1: Update `#toolsMenu` in `backend/templates/chat/index.html`**
  - Remove button for Tool #3 ("تنفيذ وتوليد الصوت الآن").
  - Update Tool #4 button title to "إنتاج فيلم وفيديو بالصور" and description to "مشاهد مصورة (وثائقي، كرتون، مانجا) وريندر Remotion".
- [ ] **Step 2: Update tool activation JavaScript handlers**
  - In `activateVideoTool()`, set `activeToolLabel` to "إنتاج فيلم وفيديو بالصور" and toast to "🎬 تم تفعيل استوديو إنتاج الفيلم والفيديو بالصور".
- [ ] **Step 3: Update and run UI tests**
  - In `tests_profile.py`, verify `chat/index.html` contains "إنتاج فيلم وفيديو بالصور" and does not contain the standalone tool button "تنفيذ وتوليد الصوت الآن".
  - Run: `./venv/bin/pytest backend/ai_studio/tests_profile.py`
  - Expected: All pass.
- [ ] **Step 4: Commit changes**
  - Run: `git add backend/templates/chat/index.html backend/ai_studio/tests_profile.py && git commit -m "feat(ui): refine tools menu, remove voice execute starter, and rename video tool to image-video"`

---

### Task 2: Create Modular Django Apps Scaffold & Models Migration

**Files:**
- Create: `backend/core/apps.py`, `backend/core/models.py`
- Create: `backend/book_drama/apps.py`, `backend/book_drama/models.py`
- Create: `backend/story_writer/apps.py`
- Create: `backend/image_video/apps.py`, `backend/image_video/models.py`
- Modify: `backend/ai_studio/models.py` (facade re-export)
- Modify: `backend/hexmedia_core/settings.py` (INSTALLED_APPS)

**Steps:**
- [ ] **Step 1: Create `backend/core` with `AIConfiguration`, `ChatThread`, `ChatMessage`**
  - Set `db_table = 'ai_studio_aiconfiguration'`, `db_table = 'ai_studio_chatthread'`, `db_table = 'ai_studio_chatmessage'`.
- [ ] **Step 2: Create `backend/book_drama` with `BookProject`, `Chapter`, `Character`**
  - Set `db_table = 'ai_studio_bookproject'`, `db_table = 'ai_studio_chapter'`, `db_table = 'ai_studio_character'`.
- [ ] **Step 3: Create `backend/image_video` with `Scene`, `TimelineState`**
  - Set `db_table = 'ai_studio_scene'`, `db_table = 'ai_studio_timelinestate'`.
- [ ] **Step 4: Create `backend/story_writer` app configuration**
  - Configure `StoryWriterConfig`.
- [ ] **Step 5: Register apps in `backend/hexmedia_core/settings.py`**
  - Add `'core'`, `'book_drama'`, `'story_writer'`, `'image_video'` to `INSTALLED_APPS`.
- [ ] **Step 6: Update `backend/ai_studio/models.py` to re-export all models**
  - Ensure all models can be imported from `ai_studio.models` as well as their respective modular apps.
- [ ] **Step 7: Run test suite to verify zero regressions**
  - Run: `./venv/bin/pytest backend/ai_studio/tests.py backend/ai_studio/tests_profile.py`
  - Expected: All pass.
- [ ] **Step 8: Commit changes**
  - Run: `git add backend/core/ backend/book_drama/ backend/story_writer/ backend/image_video/ backend/ai_studio/models.py backend/hexmedia_core/settings.py && git commit -m "refactor(arch): split monolithic models into core, book_drama, and image_video apps with db_table preservation"`

---

### Task 3: Modularize Services and Endpoints

**Files:**
- Create/Move: Services into respective apps (`book_drama/services/`, `image_video/services/`, `core/services/`)
- Update: Imports in `api.py` and `langgraph_controller.py`
- Create: Test module `backend/core/tests_modular_architecture.py` verifying multi-app imports and isolation.

**Steps:**
- [ ] **Step 1: Move/re-export book parsing logic in `book_drama/services/book_parser.py`**
- [ ] **Step 2: Move/re-export visual frames & Remotion logic in `image_video/services/`**
- [ ] **Step 3: Move/re-export memory helper in `core/services/memory_service.py`**
- [ ] **Step 4: Create `backend/core/tests_modular_architecture.py`**
  - Test importing models and services from `core`, `book_drama`, `story_writer`, `image_video`.
  - Test app registry confirms all 4 apps are installed and active.
- [ ] **Step 5: Run full `./init.sh` verification**
  - Expected: All tests pass cleanly, compileall passes.
- [ ] **Step 6: Commit changes**
  - Run: `git add backend/ && git commit -m "refactor(services): organize modular services and add architecture integrity tests"`

---

### Task 4: Documentation & Final Verification

**Files:**
- Modify: `feature_list.json`
- Modify: `progress.md`

**Steps:**
- [ ] **Step 1: Update `feature_list.json` with `feat-010` Modular Architecture**
- [ ] **Step 2: Update `progress.md` with session summary**
- [ ] **Step 3: Run final `./init.sh` harness verification**
- [ ] **Step 4: Commit and leave clean repository state**
