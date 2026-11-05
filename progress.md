# HexMedia Studio — Session Progress

## Session 3 — 2026-10-24

### Completed ✅

**M1 — Auth & Data Isolation** (prev session)
- Hybrid JWT + Django Session auth
- `/api/auth/register|login|logout|refresh|me`
- User FK on BookProject + ChatMessage (migration 0007)
- 46 tests passing

**M2 — Chat Thread Memory**
- `ChatThread` model: UUID PK, user FK, soft-delete, auto-title
- `ChatMessage.thread` FK (migration 0008)
- CRUD: `GET/POST /api/threads`, `GET /api/threads/{id}`, `GET /api/threads/{id}/messages`
- `PATCH /api/threads/{id}/rename`, `DELETE /api/threads/{id}` (soft)
- Sliding window memory: `_build_history(thread, limit=20)` 
- `chat_endpoint` wired: resume thread via `thread_id` or auto-create with AI title

**M3 — Sidebar UI & Auth Modals** (partially by subagent before quota)
- `loginModal` + `registerModal` in index.html
- `pendingPrompt` visitor onboarding flow
- `loadUserThreads()` + `switchThread()` JS functions
- Thread list grouped by Today/Yesterday/Last 7 Days
- Ctrl+K new chat, Ctrl+B sidebar toggle

### Evidence
- 46/46 Django tests pass (`python backend/manage.py test ai_studio.tests --keepdb`)
- Smoke tests: create thread → send chat → auto-title → rename → soft-delete ✅
- API import clean, migration 0008 applied
- Git commit: bbc9d8c

### Session 5 — 2026-10-24: Fix Real Gemini 3.5 Transcribe & Subtitles

### Completed ✅
- **Root Cause Diagnosed**:
  - `gemini-3.5-transcribe` is a dedicated STT model that outputs `audio_transcription` object parts (`speaker_label`, `words`, `start_offset`, `end_offset`, `text`), NOT a JSON string.
  - Previous code attempted `json.loads(response.text)` on pure text, throwing `JSONDecodeError` and silently falling back to the static hardcoded Arabic sentence.
- **Implemented Real Gemini Integration**:
  - Configured `AudioTranscriptionConfig(language_codes=..., diarization=..., word_timestamp=True)`.
  - Extracted exact spoken words, timestamps, and speaker labels (`متحدث 1`, `متحدث 2`) from `part.audio_transcription`.
  - Added multi-language translation support via `gemini-3.8-flash` preserving segment timing and speakers.
  - Tested live on user's recording: accurately transcribed `"السلام عليكم ورحمة الله وبركاته، ايه الاخبار؟"` and translated to Russian `"Мир вам, милость Аллаха и Его благословение, как дела?"`.
  - All 11 STT unit tests pass in `backend/stt/tests_stt.py`.

---

## Session 4 — 2026-10-24: Traefik HTTPS Deployment (nip.io)

### Completed ✅
- **Traefik Dynamic Routing**:
  - Added `hexmedia-http` (HTTP:80 -> HTTPS:443 308 redirect) and `hexmedia-https` (HTTPS:443 with `myresolver` ACME Let's Encrypt SSL) to `/root/motaem/traefik_data/voice_dynamic.yml`.
  - Added `hexmedia-minio-http` and `hexmedia-minio-https` for SSL asset streaming (`hexmedia-assets.169.58.32.179.nip.io`).
  - Added `hexmedia-redirect-https` middleware.
  - Zero downtime / zero interference with other live systems (`uggu.space`, telephony/voice services).
- **Django Proxy & Security Settings**:
  - `SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')`
  - `USE_X_FORWARDED_HOST = True`
  - `USE_X_FORWARDED_PORT = True`
  - `ALLOWED_HOSTS` updated with nip.io domains.
  - `CSRF_TRUSTED_ORIGINS` updated with `https://hexmedia.169.58.32.179.nip.io`, `https://hexmedia-assets.169.58.32.179.nip.io`, and `https://*.169.58.32.179.nip.io`.
  - `CORS_ALLOWED_ORIGINS` updated with nip.io domains.
  - `MINIO_PUBLIC_ENDPOINT` set to `https://hexmedia-assets.169.58.32.179.nip.io`.
- **Verification**:
  - Traefik dynamically acquired Let's Encrypt certificate for both domains.
  - HTTP `http://hexmedia.169.58.32.179.nip.io` -> 308 redirect to HTTPS.
  - HTTPS `https://hexmedia.169.58.32.179.nip.io` -> HTTP/2 200 with valid TLS.
  - HTTPS `https://hexmedia-assets.169.58.32.179.nip.io/minio/health/live` -> HTTP/2 200 with valid TLS.
  - Unbroken continuity on `uggu.space` and `app.169.58.32.179.nip.io`.

---

## Session 6 — 2026-11-05: Gemini 3.8 Flash Voice Cloning & TTS Studio Integration

### Completed ✅
- **Voice Cloning Tool in `#toolsMenu`**:
  - Added "استنساخ الصوت (Clone Your Voice)" item to the floating dock tools menu in `backend/templates/chat/index.html`.
- **4-Step Wizard Modal (`#voiceCloneModal`)**:
  - Step 1: Record reference audio (`source_audio`) with microphone (live audio level / recording timer) or upload audio file.
  - Step 2: Record mandatory biometric consent audio (`consent_audio`) reading exact Arabic phrase:
    "أنا مالك هذا الصوت وأوافق على أن تستخدم google هذا الصوت لإنشاء نموذج صوتي اصطناعي."
  - Step 3: Server converts audio to 24kHz mono 16-bit WAV using ffmpeg pipe conversion (`voice_cloner.py`), calls Gemini Voices API `client.voices.create(store=True, ...)`, verifies speaker match, and stores the `voice.id`.
  - Step 4: Audition / test voice with custom sentence, play generated sample, and save voice.
- **TTS Studio Integration (`#ttsConfigModal`)**:
  - Added dedicated "أصواتي المستنسخة (My Voices)" section at the very top of voice selection with real-time count badge.
  - Allows selecting any replicated voice for speech synthesis instead of prebuilt voices (`Puck`, `Charon`, etc.).
- **Backend Model & API Endpoints**:
  - `ClonedVoice` model in `backend/tts/models.py` (migration `0002_clonedvoice.py`).
  - `POST /api/tts/voices/clone`: Uploads source & consent audio, converts via ffmpeg, replicates via Gemini API.
  - `GET /api/tts/voices/cloned`: Returns user's cloned voices.
  - `POST /api/tts/voices/cloned/{voice_id}/test`: Audition endpoint synthesizing test phrases.
  - `DELETE /api/tts/voices/cloned/{voice_id}`: Deletes record and remote Gemini voice.
- **TTS Engine Update**:
  - `generate_voice_audio` in `backend/ai_studio/services/gemini_service.py` supports replicated voice IDs (`voice_...`) and resolves `ClonedVoice` UUIDs, preventing invalid prebuilt voice crashes.
  - Migration `0003_alter_ttsjob_voice_profile.py` expands `TTSJob.voice_profile` to `max_length=255` preventing DB truncation errors with real Gemini voice IDs.
  - Piped ffmpeg audio output corrected via `fix_wav_header_sizes` preventing 4GB duration artifacts.
  - Gemini biometric speaker mismatch errors properly bubbled as 400 Bad Request instead of masked with fake "READY" voices.
  - TTS Studio My Voices cards updated with safe UUID selectors, display names, and direct delete actions.
- **Verification**:
  - 31/31 TTS unit tests pass (`backend/tts/tests_tts.py`).
  - 204/204 total test suite passes (`./init.sh`).
  - Python compileall syntax check clean.
