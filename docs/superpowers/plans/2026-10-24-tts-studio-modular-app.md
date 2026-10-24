# TTS Studio Modular App & Long-Form Audio Stitching Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a dedicated, modular Django application (`backend/tts/`) for standalone Text-to-Speech (TTS) powered by Gemini, featuring multi-language, dialect, emotion, style, and voice configuration modal in the UI, smart Arabic diacritization, automatic sentence-boundary text chunking for texts exceeding 2500 characters, seamless audio stitching into a master audio file, and direct audio playback in chat and profile hub.

**Architecture:**
- Backend:
  - New Django app `backend/tts/` registered in `INSTALLED_APPS`.
  - Models `TTSJob` and `TTSChunk` with PostgreSQL table `tts_job` and user ownership.
  - Chunking service `backend/tts/services/chunker.py` splitting long texts (>2500 chars) on sentence/paragraph boundaries (`.`, `!`, `؟`, `\n`).
  - Audio stitcher service `backend/tts/services/audio_stitcher.py` concatenating WAV streams using Python's `wave` module with acoustic spacing.
  - Endpoints in `backend/tts/api.py`: `GET /api/tts/options`, `POST /api/tts/generate`, `GET /api/tts/history`.
- Frontend:
  - Add "🎙️ تحويل النص إلى صوت (TTS Studio)" to tools popup menu in `backend/templates/chat/index.html`.
  - Add `#ttsConfigModal` allowing user to select Language, Dialect, Voice Profile, Emotion, Delivery Style, and Custom Directives.
  - Active tool pill showing selected configuration above chat input.
  - Chat feed renderer for `TTS_AUDIO_CARD` with unified audio player, MP3 download, and chunk breakdown.

**Tech Stack:** Django, Django Ninja, Gemini Speech/TTS, Wave/PCM audio processing, MinIO S3, Tailwind CSS, Vanilla JS.

---

## Global Constraints

- Maintain all 158 existing tests with zero regressions.
- All new endpoints require JWT and Session authentication with strict user isolation.
- Preserve zero-build monolithic HTML template structure in `backend/templates/chat/index.html`.
- Repository must remain restartable from `./init.sh`.

---

### Task 1: Create `backend/tts/` App Scaffold, Models, Chunking & Stitching Services

**Files:**
- Create: `backend/tts/__init__.py`, `backend/tts/apps.py`
- Create: `backend/tts/models.py`
- Create: `backend/tts/services/__init__.py`
- Create: `backend/tts/services/chunker.py`
- Create: `backend/tts/services/audio_stitcher.py`
- Create: `backend/tts/services/tts_engine.py`
- Create: `backend/tts/tests_tts.py`
- Modify: `backend/hexmedia_core/settings.py`

**Steps:**
- [ ] **Step 1: Write unit tests in `backend/tts/tests_tts.py`**
  - Test `split_text_into_chunks` with small text (1 chunk) and large text >3000 chars (multiple chunks at sentence boundaries).
  - Test `stitch_wav_buffers` combining 2 valid WAV streams into a valid WAV header and concatenated PCM body.
  - Test `TTSJob` model creation with user ownership and choices.
- [ ] **Step 2: Run pytest to verify test failure (TDD RED)**
  - Run: `./venv/bin/pytest backend/tts/tests_tts.py`
  - Expected: Failures due to uncreated modules.
- [ ] **Step 3: Implement `backend/tts/apps.py` and register in `settings.py`**
  - Add `'tts'` to `INSTALLED_APPS`.
- [ ] **Step 4: Implement `backend/tts/models.py`**
  - `TTSJob`: `user`, `title`, `input_text`, `vocalized_text`, `language`, `dialect`, `voice_profile`, `emotion`, `delivery_style`, `custom_instructions`, `audio_url`, `duration_seconds`, `status`, `created_at`.
- [ ] **Step 5: Implement `chunker.py` and `audio_stitcher.py`**
  - `chunker.py`: clean sentence/paragraph splitter respecting `max_chars=2500`.
  - `audio_stitcher.py`: Python `wave` concatenation with silence pauses between parts.
- [ ] **Step 6: Run tests to verify passing (TDD GREEN)**
  - Run: `./venv/bin/pytest backend/tts/tests_tts.py`
  - Expected: All unit tests in `tests_tts.py` pass.
- [ ] **Step 7: Commit changes**
  - Run: `git add backend/tts/ backend/hexmedia_core/settings.py && git commit -m "feat(tts): create tts app with models, text chunker, and audio stitcher"`

---

### Task 2: Implement TTS Engine and API Endpoints

**Files:**
- Create: `backend/tts/services/tts_engine.py`
- Create: `backend/tts/api.py`
- Modify: `backend/ai_studio/api.py` (mount router or include endpoints)
- Modify: `backend/tts/tests_tts.py`

**Steps:**
- [ ] **Step 1: Add integration tests in `backend/tts/tests_tts.py`**
  - Test `GET /api/tts/options` returns language, dialect, emotion, style, voice arrays.
  - Test `POST /api/tts/generate` with small text generates audio and returns 200.
  - Test `POST /api/tts/generate` with large text (>3000 chars) chunks, stitches, and returns master audio URL.
  - Test `GET /api/tts/history` returns only authenticated user's jobs.
  - Test unauthenticated requests return 401.
- [ ] **Step 2: Implement `tts_engine.py`**
  - Auto-diacritization for Arabic using Gemini prompt when enabled.
  - Generates speech for each chunk via `generate_voice_audio`.
  - Stitches chunks via `audio_stitcher.py`.
  - Uploads master audio to MinIO and saves `TTSJob`.
- [ ] **Step 3: Implement `backend/tts/api.py` endpoints**
  - Register endpoints with Ninja router.
- [ ] **Step 4: Run tests to verify passing**
  - Run: `./venv/bin/pytest backend/tts/tests_tts.py`
  - Expected: All pass.
- [ ] **Step 5: Commit changes**
  - Run: `git add backend/tts/ backend/ai_studio/api.py && git commit -m "feat(tts): implement tts engine and api endpoints with chunking and stitching"`

---

### Task 3: Implement Frontend TTS Configuration Modal and Chat Card

**Files:**
- Modify: `backend/templates/chat/index.html`
- Modify: `backend/tts/tests_tts.py`

**Steps:**
- [ ] **Step 1: Add Tool #4 to `#toolsMenu` in `backend/templates/chat/index.html`**
  - "🎙️ تحويل النص إلى صوت (TTS Studio)"
  - Subtitle: "تخصيص كامل: لغة، لهجة، مشاعر، أسلوب وإلقاء صوتي"
  - On click: calls `openTTSConfigModal()`.
- [ ] **Step 2: Add `#ttsConfigModal` in `backend/templates/chat/index.html`**
  - Modal with obsidian dark theme and lime accent.
  - Dropdowns / selectors for:
    - اللغة (العربية، الإنجليزية، الفرنسية...)
    - اللهجة (فصحى معيارية، مصرية، خليجية، شامية، مغاربية، أمريكية...)
    - صوت المعلق (Charon, Puck, Kore, Fenrir, Aoede) مع استماع تجريبي.
    - المشاعر (طبيعي، حماسي، درامي جاد، فرح، حزين، همس).
    - أسلوب الإلقاء (وثائقي، إعلاني، قصصي، إخباري، سينمائي).
    - تعليمات وتوجيهات مخصصة (Textarea).
  - Button "تأكيد وتفعيل الأداة".
- [ ] **Step 3: Add JavaScript handlers in `backend/templates/chat/index.html`**
  - `openTTSConfigModal()`, `closeTTSConfigModal()`, `confirmTTSConfig()`.
  - Show active tool pill: `🎙️ تحويل النص لصوت [لغة • لهجة • أسلوب • صوت]`.
  - In `handleSendMessage()`, if active tool is `'tts'`, call `/api/tts/generate`.
  - Render assistant message card `TTS_AUDIO_CARD` with master audio player, MP3 download, and chunk breakdown.
- [ ] **Step 4: Add UI verification test in `backend/tts/tests_tts.py`**
  - Test `GET /` contains `#ttsConfigModal`, `#ttsLanguageSelect`, `#ttsVoiceSelect`, and TTS tool trigger.
- [ ] **Step 5: Run tests and verify**
  - Run: `./venv/bin/pytest backend/tts/tests_tts.py`
  - Expected: All pass.
- [ ] **Step 6: Commit changes**
  - Run: `git add backend/templates/chat/index.html backend/tts/tests_tts.py && git commit -m "feat(ui): add tts config modal, active pill, and audio card renderer"`

---

### Task 4: Full Verification & Documentation Update

**Files:**
- Modify: `feature_list.json`
- Modify: `progress.md`

**Steps:**
- [ ] **Step 1: Update `feature_list.json` with `feat-011` TTS Studio**
- [ ] **Step 2: Update `progress.md`**
- [ ] **Step 3: Run full harness verification `./init.sh`**
- [ ] **Step 4: Commit and finalize state**
